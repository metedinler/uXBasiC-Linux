"""Preprocessor directive effects: every directive that used to be "recorded only" (S-672) must change something observable.

Each case writes a program (plus helper files) into a private scratch directory, runs the compiler on it and checks the effect:
text on the terminal, the expanded source, the preprocess-result JSON, or files the compiler wrote below the output root.
A directive without an effect cannot pass here. Cases are grouped by the stage the effect happens in:
  P  preprocessing time (`lex` verb): diagnostics, source rewriting, templates, sections, path aliases, limits
  E  package output time (`jsw --emit-browser`): assets, manifest, shell, JSON/Markdown/WAT files, export tables
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

CASES = []
NODE = shutil.which('node')
WAT2WASM = Path(__file__).resolve().parents[2] / 'tools' / 'wabt' / 'bin' / 'wat2wasm.exe'


def fnv1a(data):
    """32-bit FNV-1a, lower case hex: the asset fingerprint the package writer adds to a copied file name."""
    h = 2166136261
    for byte in data:
        h = ((h ^ byte) * 16777619) & 0xFFFFFFFF
    return '%08x' % h


BROWSER = ('jsw', '--emit-browser')
BROWSER_WAT = ('jsw', '--emit-browser', '--emit-wat')
LOGO = bytes(range(1, 201))


def case(name, source, verb=('lex',), files=None, args=(), **expect):
    CASES.append(dict(name=name, source=source, verb=list(verb), files=files or {}, args=list(args), expect=expect))


def rel_matches(out_root, pattern):
    return sorted(out_root.glob(pattern))


# ---------------------------------------------------------------- P: diagnostics
case('warn_meta_terminal', '%%WARN_META "dikkat"\nPRINT 1\n', out_has=['WARN: %%WARN_META: dikkat'])
case('info_meta_terminal', '%%INFOMETA "bilgi"\nPRINT 1\n', out_has=['INFO: %%INFOMETA: bilgi'])
case('deprecated_used', '%%DEPRECATED "ESKI", "YENI"\nPRINT ESKI\n', out_has=['WARN: DEPRECATED: ESKI (satir 1); YENI kullanin'])
case('deprecated_unused', '%%DEPRECATED "ESKI", "YENI"\nPRINT 1\n', out_lacks=['DEPRECATED: ESKI'])
case('deprecated_not_in_string_or_comment',
     '%%DEPRECATED "ESKI"\nPRINT "ESKI"\n\' ESKI burada yorum\nPRINT 2\n', out_lacks=['DEPRECATED: ESKI'])
case('deprecated_whole_word_only', '%%DEPRECATED "ESKI"\nPRINT ESKIDEN\n', out_lacks=['DEPRECATED: ESKI'])
case('deprecated_without_new_name', '%%DEPRECATED "ESKI"\nPRINT ESKI\n', out_has=['WARN: DEPRECATED: ESKI (satir 1)'], out_lacks=['kullanin'])
case('expandlimit_allows_exact', '%%EXPANDLIMIT 5\n%%FOR K = 1 TO 5\nPRINT {{K}}\n%%ENDFOR\n',
     expanded='PRINT 1\nPRINT 2\nPRINT 3\nPRINT 4\nPRINT 5')
case('expandlimit_stops_overflow', '%%EXPANDLIMIT 5\n%%FOR K = 1 TO 6\nPRINT {{K}}\n%%ENDFOR\n', error='PREPROCESSOR_FOR_ITERATION_LIMIT')
case('expandlimit_applies_to_repeat', '%%EXPANDLIMIT 3\n%%REPEAT 4\nPRINT 1\n%%ENDREPEAT\n', error='PREPROCESSOR_REPEAT_ITERATION_LIMIT')
case('expandlimit_invalid', '%%EXPANDLIMIT 0\nPRINT 1\n', error='PREPROCESSOR_EXPANDLIMIT_INVALID')
case('expandlimit_not_a_number', '%%EXPANDLIMIT bol\nPRINT 1\n', error='PREPROCESSOR_EXPANDLIMIT_INVALID')

# ---------------------------------------------------------------- P: paths
case('path_alias_include', '%%PATH_ALIAS "@lib" AS "lib"\n%%INCLUDE "@lib/x.uxbh"\n', files={'lib/x.uxbh': b'PRINT 42\n'}, expanded='PRINT 42')
case('path_alias_embedtext', '%%PATH_ALIAS "@d" AS "data"\n%%EMBEDTEXT "@d/t.txt" AS TXT\nPRINT TXT\n',
     files={'data/t.txt': b'merhaba'}, expanded='PRINT merhaba')
case('path_alias_hashfile', '%%PATH_ALIAS "@d" AS "data"\n%%HASHFILE "@d/t.txt" AS H\nPRINT H\n',
     files={'data/t.txt': b'abc'}, expanded='PRINT 1A47E90B')
case('path_alias_config_file', '%%PATH_ALIAS "@c" AS "cfg"\n%%CONFIG_FILE "@c/a.cfg"\nPRINT ADI\n',
     files={'cfg/a.cfg': b'ADI=ucuncu\n'}, expanded='PRINT ucuncu')
case('path_alias_unknown_is_error', '%%INCLUDE "@yok/x.uxbh"\n', error='LEX_INCLUDE_FAILED')

# ---------------------------------------------------------------- P: features, sections, templates
case('feature_defines_macro', '%%FEATURE hizli\n%%IF FEATURE_HIZLI\nPRINT 1\n%%ELSE\nPRINT 2\n%%ENDIF\n', expanded='PRINT 1')
case('feature_absent_is_false', '%%IF FEATURE_HIZLI\nPRINT 1\n%%ELSE\nPRINT 2\n%%ENDIF\n', expanded='PRINT 2')
case('section_sets_default_block_section', '%%SECTION HEAD\n%%HTML_BEGIN\n<meta>\n%%HTML_END\n%%ENDSECTION\nPRINT 1\n',
     expanded='PRINT 1', json=[('pr.json', ['blocks', 0, 'section'], 'HEAD')])
case('section_explicit_wins', '%%SECTION HEAD\n%%HTML_BEGIN "x.html" BODY\n<b/>\n%%HTML_END\n%%ENDSECTION\nPRINT 1\n',
     json=[('pr.json', ['blocks', 0, 'section'], 'BODY')])
case('section_ends_at_endsection', '%%SECTION HEAD\n%%ENDSECTION\n%%HTML_BEGIN\n<b/>\n%%HTML_END\nPRINT 1\n',
     json=[('pr.json', ['blocks', 0, 'section'], 'BODY')])
case('section_nested_uses_inner', '%%SECTION HEAD\n%%SECTION BODY\n%%JS_LINE x\n%%HTML_BEGIN\n<i/>\n%%HTML_END\n%%ENDSECTION\n%%ENDSECTION\nPRINT 1\n',
     json=[('pr.json', ['blocks', 1, 'section'], 'BODY')])
case('section_unmatched_end', '%%ENDSECTION\nPRINT 1\n', error='META_UNMATCHED_END')
case('section_requires_name', '%%SECTION\nPRINT 1\n', error='PREPROCESSOR_SECTION_NAME_MISSING')
case('template_inline_use', '%%TEMPLATE_BEGIN kart\nPRINT {{N}}\n%%TEMPLATE_END\n%%SET N = 7\n%%TEMPLATE_USE kart\n', expanded='PRINT 7')
case('template_use_twice_with_other_values',
     '%%TEMPLATE_BEGIN kart\nPRINT {{N}}\n%%TEMPLATE_END\n%%SET N = 1\n%%TEMPLATE_USE kart\n%%SET N = 2\n%%TEMPLATE_USE kart\n',
     expanded='PRINT 1\nPRINT 2')
case('template_body_never_reaches_source', '%%TEMPLATE_BEGIN kart\nPRINT 999\n%%TEMPLATE_END\nPRINT 1\n', expanded='PRINT 1')
case('template_body_may_hold_directives', '%%TEMPLATE_BEGIN kart\n%%DEFINE W 8\nPRINT W\n%%TEMPLATE_END\n%%TEMPLATE_USE kart\n', expanded='PRINT 8')
case('template_from_file', '%%TEMPLATE kart "t.tpl"\n%%SET N = 5\n%%TEMPLATE_USE kart\n', files={'t.tpl': b'PRINT {{N}}\n'}, expanded='PRINT 5')
case('template_file_via_alias', '%%PATH_ALIAS "@t" AS "tpl"\n%%TEMPLATE kart "@t/k.tpl"\n%%SET N = 6\n%%TEMPLATE_USE kart\n',
     files={'tpl/k.tpl': b'PRINT {{N}}\n'}, expanded='PRINT 6')
case('template_name_only_is_error', '%%TEMPLATE kart\nPRINT 1\n', error='PREPROCESSOR_TEMPLATE_FILE_MISSING')
case('template_file_missing', '%%TEMPLATE kart "yok.tpl"\nPRINT 1\n', error='PREPROCESSOR_TEMPLATE_FILE_NOT_FOUND')
case('template_undefined', '%%TEMPLATE_USE yok\nPRINT 1\n', error='PREPROCESSOR_TEMPLATE_UNDEFINED')
case('template_placeholder_undefined', '%%TEMPLATE_BEGIN kart\nPRINT {{YOK}}\n%%TEMPLATE_END\n%%TEMPLATE_USE kart\n',
     error='PREPROCESSOR_TEMPLATE_PLACEHOLDER_UNDEFINED')
case('template_non_identifier_braces_are_literal', '%%TEMPLATE_BEGIN kart\nPRINT "{{ 1 + 2 }}"\n%%TEMPLATE_END\n%%TEMPLATE_USE kart\n',
     expanded='PRINT "{{ 1 + 2 }}"')
case('template_into_file', '%%TEMPLATE_BEGIN kart\n<p>{{N}}</p>\n%%TEMPLATE_END\n%%SET N = 3\n%%TEMPLATE_USE kart INTO "k.html"\nPRINT 1\n',
     expanded='PRINT 1', out_files=[('**/generated/k.html', b'<p>3</p>\n')])
case('template_into_unsafe_path', '%%TEMPLATE_BEGIN kart\nx\n%%TEMPLATE_END\n%%TEMPLATE_USE kart INTO "../k.html"\n', error='PREPROCESSOR_TEMPLATE_PATH_UNSAFE')
case('template_invalid_name', '%%TEMPLATE_BEGIN "bir sablon"\nx\n%%TEMPLATE_END\n', error='PREPROCESSOR_TEMPLATE_NAME_INVALID')

# ---------------------------------------------------------------- P: block bookkeeping flags
case('source_map_tags_following_blocks', '%%SOURCE_MAP "ana:1"\n%%HTML_BEGIN\n<b/>\n%%HTML_END\nPRINT 1\n',
     json=[('pr.json', ['blocks', 0, 'sourceTag'], 'ana:1')])
case('source_map_changes_between_blocks',
     '%%SOURCE_MAP "a"\n%%HTML_BEGIN\n<b/>\n%%HTML_END\n%%SOURCE_MAP "b"\n%%HTML_BEGIN\n<i/>\n%%HTML_END\nPRINT 1\n',
     json=[('pr.json', ['blocks', 0, 'sourceTag'], 'a'), ('pr.json', ['blocks', 1, 'sourceTag'], 'b')])
case('minify_syntax_is_checked', '%%MINIFY FOO ON\nPRINT 1\n', error='PREPROCESSOR_MINIFY_SYNTAX')
case('minify_accepts_known_kinds', '%%MINIFY JS ON\n%%MINIFY CSS OFF\n%%MINIFY ALL ON\nPRINT 1\n', expanded='PRINT 1')

# ---------------------------------------------------------------- P: required manifest keys, output folder safety, generated files
case('manifest_require_satisfied', '%%MANIFEST_SET ad = "x"\n%%MANIFEST_REQUIRE ad\nPRINT 1\n', expanded='PRINT 1')
case('manifest_require_nested_key_satisfied', '%%BUNDLE_NAME "p"\n%%MANIFEST_REQUIRE "bundle.name"\nPRINT 1\n', expanded='PRINT 1')
case('manifest_require_section_satisfied', '%%CAPABILITY storage ON\n%%MANIFEST_REQUIRE capabilities\nPRINT 1\n', expanded='PRINT 1')
case('manifest_require_missing', '%%MANIFEST_REQUIRE ad\nPRINT 1\n', error='MANIFEST_REQUIRED_MISSING')
case('manifest_require_checked_after_whole_program', '%%MANIFEST_REQUIRE ad\n%%MANIFEST_SET ad = "x"\nPRINT 1\n', expanded='PRINT 1')
case('outdir_unsafe_is_rejected', '%%OUTDIR "../disari"\nPRINT 1\n', error='PREPROCESSOR_OUTDIR_UNSAFE')
case('gen_file_without_block_is_created_empty', '%%GEN_FILE "o.txt" TXT\nPRINT 1\n', out_has=['GEN_FILE_NO_BLOCK'],
     out_files=[('**/generated/o.txt', b'')])
case('gen_file_with_block_gets_its_text', '%%GEN_FILE "o.txt" TXT\n%%GEN_BLOCK "o.txt"\nicerik\n%%GEN_END\nPRINT 1\n',
     out_lacks=['GEN_FILE_NO_BLOCK'], out_files=[('**/generated/o.txt', b'icerik\n')])
case('gen_file_json_valid', '%%GEN_FILE "o.json" JSON\n%%GEN_BLOCK "o.json"\n{"a": 1}\n%%GEN_END\nPRINT 1\n',
     out_files=[('**/generated/o.json', b'{"a": 1}\n')])
case('gen_file_json_invalid', '%%GEN_FILE "o.json" JSON\n%%GEN_BLOCK "o.json"\nbu json degil\n%%GEN_END\nPRINT 1\n', error='GEN_FILE_KIND_MISMATCH')

# ---------------------------------------------------------------- E: page, manifest and declared package files (jsw --emit-browser)
PAGE = '**/web/browser/index.html'
MANIFEST = '**/web/browser/manifest.json'
case('bundle_in_page_and_manifest',
     '%%BUNDLE_NAME "Paket"\n%%BUNDLE_VERSION "2.0"\n%%BUNDLE_ID "pk.1"\n%%AUTHOR "Ayse"\n%%LICENSE "MIT"\n%%BUILD_ID "b7"\nPRINT 1\n', verb=BROWSER,
     out_text_has=[(PAGE, '<title>Paket</title>'), (PAGE, '<meta name="author" content="Ayse">'), (PAGE, '<meta name="version" content="2.0">'),
                   (PAGE, '<meta name="license" content="MIT">'), (PAGE, '<meta name="build-id" content="b7">'), (PAGE, '<meta name="bundle-id" content="pk.1">')],
     out_json=[(MANIFEST, ['bundle', 'name'], 'Paket'), (MANIFEST, ['bundle', 'version'], '2.0'), (MANIFEST, ['bundle', 'id'], 'pk.1'),
               (MANIFEST, ['bundle', 'author'], 'Ayse'), (MANIFEST, ['bundle', 'license'], 'MIT'), (MANIFEST, ['bundle', 'buildId'], 'b7')])
case('page_title_default', 'PRINT 1\n', verb=BROWSER, out_text_has=[(PAGE, '<title>uXBasic Browser Output</title>')])
case('csp_meta_and_manifest', '%%CSP "default-src \'self\'"\nPRINT 1\n', verb=BROWSER,
     out_text_has=[(PAGE, '<meta http-equiv="Content-Security-Policy" content="default-src \'self\'">')],
     out_json=[(MANIFEST, ['security', 'csp'], "default-src 'self'")])
case('security_note_comment_and_manifest', '%%SECURITY_NOTE "yalniz deneme"\nPRINT 1\n', verb=BROWSER,
     out_text_has=[(PAGE, '<!-- security note: yalniz deneme -->')], out_json=[(MANIFEST, ['security', 'note'], ['yalniz deneme'])])
case('capability_table', '%%CAPABILITY storage ON\n%%CAPABILITY camera OFF\nPRINT 1\n', verb=BROWSER,
     out_text_has=[(PAGE, 'globalThis.uxbCapabilities'), (PAGE, '"storage": true'), (PAGE, '"camera": false')],
     out_json=[(MANIFEST, ['capabilities', 'storage'], True), (MANIFEST, ['capabilities', 'camera'], False)])
case('feature_table', '%%FEATURE hizli\nPRINT 1\n', verb=BROWSER,
     out_text_has=[(PAGE, 'globalThis.uxbFeatures'), (PAGE, '"hizli": true')], out_json=[(MANIFEST, ['features', 'hizli'], True)])
case('route_table', '%%ROUTE ana /index\n%%ROUTE ayar /ayar\nPRINT 1\n', verb=BROWSER,
     out_text_has=[(PAGE, 'globalThis.uxbRoutes'), (PAGE, 'globalThis.uxbRoute = function'), (PAGE, '"ana": "/index"')],
     out_json=[(MANIFEST, ['routes', 'ana'], '/index'), (MANIFEST, ['routes', 'ayar'], '/ayar')])
case('script_text_cannot_close_the_script_element', '%%ROUTE ana /</script>\nPRINT 1\n', verb=BROWSER,
     out_text_has=[(PAGE, '"ana": "/<\\/script>"')])
case('api_endpoint_helper', '%%API_ENDPOINT Kaydet POST /api/kaydet\nPRINT 1\n', verb=BROWSER,
     out_text_has=[(PAGE, 'globalThis.uxbApi'), (PAGE, '"url": "/api/kaydet"'), (PAGE, 'fetch(ep.url, opts)')],
     out_json=[(MANIFEST, ['api', 'Kaydet', 'method'], 'POST'), (MANIFEST, ['api', 'Kaydet', 'url'], '/api/kaydet')])
case('docs_readme_and_description', '%%DOC description "Kisa tanim"\n%%DOC kullanim "Ac ve calistir"\n%%BUNDLE_NAME "Paket"\nPRINT 1\n', verb=BROWSER,
     out_text_has=[(PAGE, '<meta name="description" content="Kisa tanim">'), ('**/web/README.md', '# Paket'), ('**/web/README.md', 'Kisa tanim'),
                   ('**/web/README.md', '## kullanim'), ('**/web/README.md', 'Ac ve calistir')],
     out_json=[(MANIFEST, ['docs', 'kullanim'], 'Ac ve calistir')])
case('readme_of_the_author_is_not_overwritten', '%%DOC description "Kisa tanim"\nPRINT 1\n', verb=BROWSER, args=['--html-out', 'pk/page.html', '--js-out', 'pk/o.js'],
     files={'pk/README.md': 'benim README dosyam\n'.encode()}, out_has=['PREPROCESSOR_README_EXISTS'],
     cwd_files=[('pk/README.md', 'benim README dosyam\n'.encode()), ('pk/page.html', None)])
case('readme_generated_earlier_is_replaced', '%%DOC description "Yeni"\nPRINT 1\n', verb=BROWSER, args=['--html-out', 'pk/page.html', '--js-out', 'pk/o.js'],
     files={'pk/README.md': '<!-- uxb package readme -->\n# eski\n'.encode()}, out_lacks=['PREPROCESSOR_README_EXISTS'],
     out_text_has=[], cwd_files=[('pk/README.md', None)])
case('custom_page_path_keeps_the_package_beside_it', '%%TEST_EXPECT "a"\n%%ASSET_COPY "logo.bin", "img/logo.bin"\nPRINT 1\n', verb=BROWSER,
     args=['--html-out', 'pk/page.html', '--js-out', 'pk/o.js'], files={'logo.bin': LOGO},
     cwd_files=[('pk/expect.txt', b'a\n'), ('pk/img/logo.bin', LOGO), ('pk/page.html', None)])
case('test_expect_file_and_manifest', '%%TEST_EXPECT "ilk"\n%%TEST_EXPECT "ikinci"\nPRINT 1\n', verb=BROWSER,
     out_files=[('**/web/expect.txt', b'ilk\nikinci\n')], out_json=[(MANIFEST, ['tests', 'expect'], ['ilk', 'ikinci'])])
case('manifest_set_nested', '%%MANIFEST_SET bundle.etiket = "x"\n%%MANIFEST_SET renk = "mavi"\nPRINT 1\n', verb=BROWSER,
     out_json=[(MANIFEST, ['bundle', 'etiket'], 'x'), (MANIFEST, ['meta', 'renk'], 'mavi')])
case('source_tag_comments_in_page', '%%SOURCE_MAP "etiket1"\n%%HTML_BEGIN\n<b>kalin</b>\n%%HTML_END\nPRINT 1\n', verb=BROWSER,
     out_text_has=[(PAGE, '<!-- src: etiket1 -->\n<b>kalin</b>')], out_json=[(MANIFEST, ['preprocess_blocks', 0, 'sourceTag'], 'etiket1')])

# assets
case('asset_copy_to_target', '%%ASSET_COPY "logo.bin", "img/logo.bin"\nPRINT 1\n', verb=BROWSER, files={'logo.bin': LOGO},
     out_files=[('**/web/browser/img/logo.bin', LOGO)],
     out_json=[(MANIFEST, ['preprocess_assets', 0, 'status'], 'COPIED'), (MANIFEST, ['preprocess_assets', 0, 'bytes'], 200),
               (MANIFEST, ['preprocess_assets', 0, 'hash'], fnv1a(LOGO)), (MANIFEST, ['preprocess_assets', 0, 'final'], 'img/logo.bin')])
case('asset_file_default_target_is_source_path', '%%ASSET_FILE "img/x.bin"\nPRINT 1\n', verb=BROWSER, files={'img/x.bin': LOGO},
     out_files=[('**/web/browser/img/x.bin', LOGO)])
case('asset_kinds_are_recorded', '%%ASSET_IMAGE "p.bin"\n%%ASSET_AUDIO "s.bin"\nPRINT 1\n', verb=BROWSER, files={'p.bin': LOGO, 's.bin': LOGO},
     out_files=[('**/web/browser/p.bin', LOGO), ('**/web/browser/s.bin', LOGO)],
     out_json=[(MANIFEST, ['preprocess_assets', 0, 'kind'], 'IMAGE'), (MANIFEST, ['preprocess_assets', 1, 'kind'], 'AUDIO')])
case('asset_root_is_searched', '%%ASSET_ROOT "dosyalar"\n%%ASSET_COPY "logo.bin"\nPRINT 1\n', verb=BROWSER, files={'dosyalar/logo.bin': LOGO},
     out_files=[('**/web/browser/logo.bin', LOGO)])
case('path_alias_in_asset_sources', '%%PATH_ALIAS "@d" AS "dosyalar"\n%%ASSET_COPY "@d/logo.bin", "logo.bin"\n%%COPY_DIR "@d/alt" TO "kopya"\n%%LICENSEFILE "@d/LISANS.txt"\nPRINT 1\n',
     verb=BROWSER, files={'dosyalar/logo.bin': LOGO, 'dosyalar/alt/a.txt': b'A', 'dosyalar/LISANS.txt': b'MIT\n'},
     out_files=[('**/web/browser/logo.bin', LOGO), ('**/web/browser/kopya/a.txt', b'A'), ('**/web/LICENSE', b'MIT\n')])
case('asset_space_separator_is_rejected', '%%ASSET_COPY "logo.bin" "img/logo.bin"\nPRINT 1\n', verb=BROWSER, files={'logo.bin': LOGO}, error='PREPROCESSOR_ASSET_SEPARATOR')
case('asset_missing_is_a_warning', '%%ASSET_COPY "yok.bin"\nPRINT 1\n', verb=BROWSER,
     out_has=['PREPROCESSOR_ASSET_MISSING: yok.bin'], out_json=[(MANIFEST, ['preprocess_assets', 0, 'status'], 'MISSING')])
case('asset_require_missing_is_an_error', '%%ASSET_REQUIRE "yok.bin"\nPRINT 1\n', verb=BROWSER, error='ASSET_REQUIRED_MISSING')
case('require_asset_missing_is_an_error', '%%REQUIRE_ASSET "yok.bin"\nPRINT 1\n', verb=BROWSER, error='ASSET_REQUIRED_MISSING')
case('require_asset_present_is_copied', '%%REQUIRE_ASSET "logo.bin" AS "ek/logo.bin"\nPRINT 1\n', verb=BROWSER, files={'logo.bin': LOGO},
     out_files=[('**/web/browser/ek/logo.bin', LOGO)])
case('asset_target_escape_is_blocked', '%%ASSET_COPY "logo.bin", "../disari.bin"\nPRINT 1\n', verb=BROWSER, files={'logo.bin': LOGO}, error='path escape blocked')
case('html_image_links_the_copied_file', '%%HTMLIMAGE "L1", "img/logo.bin"\nPRINT 1\n', verb=BROWSER, files={'img/logo.bin': LOGO},
     out_files=[('**/web/browser/img/logo.bin', LOGO)], out_text_has=[(PAGE, '<img id="L1" src="img/logo.bin">')])
case('html_audio_links_the_copied_file', '%%HTMLAUDIO "A1", "snd/a.bin"\nPRINT 1\n', verb=BROWSER, files={'snd/a.bin': LOGO},
     out_files=[('**/web/browser/snd/a.bin', LOGO)], out_text_has=[(PAGE, '<audio id="A1" src="snd/a.bin" controls></audio>')])
case('fingerprint_renames_the_copy', '%%FINGERPRINT_ASSETS ON\n%%ASSET_COPY "logo.bin", "img/logo.bin"\nPRINT 1\n', verb=BROWSER, files={'logo.bin': LOGO},
     out_files=[('**/web/browser/img/logo.%s.bin' % fnv1a(LOGO), LOGO)], out_files_absent=['**/web/browser/img/logo.bin'],
     out_json=[(MANIFEST, ['preprocess_assets', 0, 'final'], 'img/logo.%s.bin' % fnv1a(LOGO))])
case('fingerprint_rewrites_the_page_link', '%%FINGERPRINT_ASSETS ON\n%%HTMLIMAGE "L1", "img/logo.bin"\nPRINT 1\n', verb=BROWSER, files={'img/logo.bin': LOGO},
     out_text_has=[(PAGE, '<img id="L1" src="img/logo.%s.bin">' % fnv1a(LOGO))])
case('fingerprint_off_keeps_the_name', '%%FINGERPRINT_ASSETS OFF\n%%ASSET_COPY "logo.bin", "img/logo.bin"\nPRINT 1\n', verb=BROWSER, files={'logo.bin': LOGO},
     out_files=[('**/web/browser/img/logo.bin', LOGO)])
case('copy_dir_copies_the_tree', '%%COPY_DIR "dos" TO "kopya"\nPRINT 1\n', verb=BROWSER, files={'dos/a.txt': b'A', 'dos/alt/b.txt': b'B'},
     out_files=[('**/web/browser/kopya/a.txt', b'A'), ('**/web/browser/kopya/alt/b.txt', b'B')])
case('copy_dir_missing_is_a_warning', '%%COPY_DIR "yok" TO "kopya"\nPRINT 1\n', verb=BROWSER, out_has=['PREPROCESSOR_ASSET_MISSING: yok'])
case('license_file_is_copied_to_the_package_root', '%%LICENSEFILE "LISANS.txt"\nPRINT 1\n', verb=BROWSER, files={'LISANS.txt': b'MIT metni\n'},
     out_files=[('**/web/LICENSE', b'MIT metni\n')])
case('license_file_missing_is_an_error', '%%LICENSEFILE "LISANS.txt"\nPRINT 1\n', verb=BROWSER, error='ASSET_REQUIRED_MISSING')
case('sandbox_root_allows_inside_inputs', '%%SANDBOX_ROOT "kutu"\n%%ASSET_COPY "kutu/ic.bin", "ic.bin"\nPRINT 1\n', verb=BROWSER,
     files={'kutu/ic.bin': LOGO}, out_files=[('**/web/browser/ic.bin', LOGO)])
case('sandbox_root_blocks_outside_inputs', '%%SANDBOX_ROOT "kutu"\n%%ASSET_COPY "disarida.bin", "d.bin"\nPRINT 1\n', verb=BROWSER,
     files={'kutu/ic.bin': LOGO, 'disarida.bin': LOGO}, error='ASSET_SANDBOX_ESCAPE')

# data, JSON, Markdown, WAT files
case('data_json_from_set_and_array',
     '%%JSON_SET ad "Ali"\n%%JSON_SET yas 7\n%%JSON_ARRAY_BEGIN renkler\nkirmizi\nyesil\n%%JSON_ARRAY_END\nPRINT 1\n', verb=BROWSER,
     out_json=[('**/web/browser/data.json', ['ad'], 'Ali'), ('**/web/browser/data.json', ['yas'], 7),
               ('**/web/browser/data.json', ['renkler'], ['kirmizi', 'yesil'])],
     out_text_has=[(PAGE, 'globalThis.uxbDataPath = "data.json"')])
case('data_json_file_name_is_chosen', '%%DATA_JSON "veri/d.json"\n%%JSON_SET ad "Ali"\nPRINT 1\n', verb=BROWSER,
     out_json=[('**/web/browser/veri/d.json', ['ad'], 'Ali')], out_text_has=[(PAGE, 'globalThis.uxbDataPath = "veri/d.json"')])
case('json_block_is_written', '%%JSON_BEGIN "ayar.json"\n{"a": 1}\n%%JSON_END\nPRINT 1\n', verb=BROWSER,
     out_files=[('**/web/browser/ayar.json', b'{"a": 1}\n')])
case('json_block_invalid_is_rejected', '%%JSON_BEGIN "ayar.json"\n{"a": \n%%JSON_END\nPRINT 1\n', verb=BROWSER, error='JSON_BLOCK_INVALID')
MD_TEXT = '# Baslik\nBir **kalin** ve *egik* yazi, [baglanti](http://x.y) ve `kod`.\n- madde bir\n- madde iki\n\n1. bir\n2. iki\n\n```\n<b>ham</b>\n```\n'
case('markdown_block_renders_html', '%%MD_BEGIN "n.md"\n' + MD_TEXT + '%%MD_END\nPRINT 1\n', verb=BROWSER,
     out_files=[('**/web/browser/n.md', MD_TEXT.encode())],
     out_text_has=[('**/web/browser/n.html', '<h1>Baslik</h1>'), ('**/web/browser/n.html', '<strong>kalin</strong>'), ('**/web/browser/n.html', '<em>egik</em>'),
                   ('**/web/browser/n.html', '<a href="http://x.y">baglanti</a>'), ('**/web/browser/n.html', '<code>kod</code>'),
                   ('**/web/browser/n.html', '<ul>\n<li>madde bir</li>\n<li>madde iki</li>\n</ul>'), ('**/web/browser/n.html', '<ol>\n<li>bir</li>\n<li>iki</li>\n</ol>'),
                   ('**/web/browser/n.html', '<pre><code>&lt;b&gt;ham&lt;/b&gt;\n</code></pre>'), ('**/web/browser/n.html', '<title>Baslik</title>')])
case('md_safe_on_escapes_raw_html', '%%MD_SAFE ON\n%%MD_BEGIN "n.md"\nmerhaba <script>alert(1)</script> dunya\n%%MD_END\nPRINT 1\n', verb=BROWSER,
     out_text_has=[('**/web/browser/n.html', '&lt;script&gt;alert(1)&lt;/script&gt;')], out_text_lacks=[('**/web/browser/n.html', '<script>alert')])
case('md_safe_off_passes_raw_html', '%%MD_SAFE OFF\n%%MD_BEGIN "n.md"\nmerhaba <b>kalin</b> dunya\n%%MD_END\nPRINT 1\n', verb=BROWSER,
     out_text_has=[('**/web/browser/n.html', '<b>kalin</b>')])
case('md_script_links_are_not_linked', '%%MD_BEGIN "n.md"\n[tikla](javascript:alert(1))\n%%MD_END\nPRINT 1\n', verb=BROWSER,
     out_text_lacks=[('**/web/browser/n.html', 'href="javascript:')])
case('md_css_is_linked_and_copied', '%%MD_CSS "stil.css"\n%%MD_BEGIN "n.md"\n# Baslik\n%%MD_END\nPRINT 1\n', verb=BROWSER, files={'stil.css': b'body{color:red}\n'},
     out_text_has=[('**/web/browser/n.html', '<link rel="stylesheet" href="stil.css">')], out_files=[('**/web/browser/stil.css', b'body{color:red}\n')])
case('wat_block_is_written_to_the_wasm_folder', '%%ALLOW_RAW_WAT ON\n%%WAT_BEGIN "x.wat"\n(module)\n%%WAT_END\nPRINT 1\n', verb=BROWSER_WAT,
     out_files=[('**/web/wasm/x.wat', b'(module)\n')])

# entry files, output folder, minify
case('style_entry_is_a_linked_file', '%%STYLE_ENTRY "site.css"\n%%CSS_RULE "body", "color:red"\nPRINT 1\n', verb=BROWSER,
     out_text_has=[(PAGE, '<link rel="stylesheet" href="site.css">'), ('**/web/browser/site.css', 'body { color:red }')], out_text_lacks=[(PAGE, '<style>')],
     out_json=[(MANIFEST, ['entries', 'css'], 'site.css')])
case('style_inline_without_entry', '%%CSS_RULE "body", "color:red"\nPRINT 1\n', verb=BROWSER, out_text_has=[(PAGE, '<style>\nbody { color:red }')])
case('script_entry_is_a_linked_file', '%%SCRIPT_ENTRY "app.js"\n%%JS_LINE console.log("kullanici");\nPRINT 1\n', verb=BROWSER,
     out_text_has=[(PAGE, '<script src="app.js"></script>'), ('**/web/browser/app.js', 'console.log("kullanici");')],
     out_json=[(MANIFEST, ['entries', 'js'], 'app.js')])
case('script_inline_without_entry', '%%JS_LINE console.log("kullanici");\nPRINT 1\n', verb=BROWSER,
     out_text_has=[(PAGE, '<script>\nconsole.log("kullanici");')])
case('browser_entry_renames_the_page', '%%BROWSER_ENTRY "uygulama.html"\nPRINT 1\n', verb=BROWSER,
     out_files=[('**/web/browser/uygulama.html', None)], out_files_absent=['**/web/browser/index.html'], out_json=[(MANIFEST, ['entries', 'html'], 'uygulama.html')])
case('outdir_moves_the_package', '%%OUTDIR "paket1"\nPRINT 1\n', verb=BROWSER,
     out_files=[('paket1/browser/index.html', None), ('paket1/browser/manifest.json', None), ('paket1/js/output.js', None), ('paket1/js/ux_runtime.js', None)],
     out_files_absent=['**/web/browser/index.html'])
case('outdir_nested_folder', '%%OUTDIR "a/b"\nPRINT 1\n', verb=BROWSER, out_files=[('a/b/browser/index.html', None)])
case('minify_js_shortens_program_and_runtime', '%%MINIFY JS ON\nPRINT 1\n', verb=BROWSER,
     out_text_lacks=[('**/web/js/output.js', '// Generated by uXBasic'), ('**/web/js/ux_runtime.js', '\n    //')], node_check=['**/web/js/output.js', '**/web/js/ux_runtime.js'])
case('minify_js_keeps_continued_string_lines', '%%MINIFY JS ON\n%%ALLOW_RAW_JS ON\n%%JS_BEGIN\n// yorum satiri\nconst s = "a\\\n    b";\n%%JS_END\nPRINT 1\n', verb=BROWSER,
     out_text_has=[(PAGE, 'const s = "a\\\n    b";')], out_text_lacks=[(PAGE, 'yorum satiri')])
case('minify_js_off_keeps_comments', 'PRINT 1\n', verb=BROWSER, out_text_has=[('**/web/js/output.js', '// Generated by uXBasic')])
case('minify_css_squeezes_rules', '%%MINIFY CSS ON\n%%CSS_BEGIN\n/* yorum */\nbody {\n  color: red;\n}\n%%CSS_END\nPRINT 1\n', verb=BROWSER,
     out_text_has=[(PAGE, 'body{color: red;}')], out_text_lacks=[(PAGE, 'yorum')])
case('minify_html_drops_comments_and_indent', '%%MINIFY HTML ON\n%%HTML_BEGIN\n<!-- gizli -->\n   <b>x</b>\n%%HTML_END\nPRINT 1\n', verb=BROWSER,
     out_text_has=[(PAGE, '\n<b>x</b>\n')], out_text_lacks=[(PAGE, 'gizli'), (PAGE, '   <b>x</b>')])
case('minify_all', '%%MINIFY ALL ON\n%%CSS_BEGIN\n/* yorum */\nbody {\n  color: red;\n}\n%%CSS_END\nPRINT 1\n', verb=BROWSER,
     out_text_has=[(PAGE, 'body{color: red;}')], out_text_lacks=[('**/web/js/output.js', '// Generated by uXBasic')], node_check=['**/web/js/output.js'])

# notes, exports, host imports, raw WAT functions
case('emitnote_in_page_js_and_wat', '%%TARGET WEB\n%%EMITNOTE "bilgi notu"\nPRINT 1\n', verb=BROWSER_WAT,
     out_text_has=[(PAGE, '<!-- bilgi notu -->'), ('**/web/js/output.js', '// bilgi notu'), ('**/web/wasm/output.wat', ';; bilgi notu')])
case('emitnote_of_another_target_is_not_written', '%%TARGET JS\n%%EMITNOTE "yalniz js"\nPRINT 1\n', verb=BROWSER_WAT,
     out_text_has=[('**/web/js/output.js', '// yalniz js')], out_text_lacks=[(PAGE, 'yalniz js'), ('**/web/wasm/output.wat', 'yalniz js')])
ADD_TWO = 'FUNCTION AddTwo(a AS I32, b AS I32) AS I32\n    RETURN a + b\nEND FUNCTION\nPRINT AddTwo(2, 3)\n'
case('export_basic_publishes_the_function', '%%EXPORT_BASIC AddTwo AS "I32(I32,I32)"\n' + ADD_TWO, verb=BROWSER_WAT,
     out_text_has=[('**/web/js/output.js', 'globalThis.uxbExports["AddTwo"] = function'), ('**/web/js/output.js', '__uxbUser["ADDTWO"]'),
                   ('**/web/wasm/output.wat', '(export "AddTwo" (func $ADDTWO))')],
     out_json=[(MANIFEST, ['exports', 'AddTwo', 'signature'], 'I32(I32,I32)'), (MANIFEST, ['exports', 'AddTwo', 'callableFromJs'], True)],
     node_check=['**/web/js/output.js'])
case('export_basic_sub_has_no_result', '%%EXPORT_BASIC Say AS "VOID(I32)"\nSUB Say(n AS I32)\n    PRINT n\nEND SUB\nSay(3)\n', verb=BROWSER,
     out_text_has=[('**/web/js/output.js', 'globalThis.uxbExports["Say"] = function')])
case('export_basic_missing_function', '%%EXPORT_BASIC Yok AS "I32()"\n' + ADD_TWO, verb=BROWSER, error='EXPORT_BASIC_FUNCTION_MISSING')
case('export_basic_signature_mismatch', '%%EXPORT_BASIC AddTwo AS "I32(I32)"\n' + ADD_TWO, verb=BROWSER, error='EXPORT_BASIC_SIGNATURE_MISMATCH')
case('export_basic_result_mismatch', '%%EXPORT_BASIC AddTwo AS "F64(I32,I32)"\n' + ADD_TWO, verb=BROWSER, error='EXPORT_BASIC_SIGNATURE_MISMATCH')
case('export_basic_signature_invalid', '%%EXPORT_BASIC AddTwo AS "tamsayi"\n' + ADD_TWO, verb=BROWSER, error='EXPORT_BASIC_SIGNATURE_INVALID')
case('export_basic_also_in_plain_js', '%%EXPORT_BASIC AddTwo AS "I32(I32,I32)"\n' + ADD_TWO, verb=('jsw',),
     out_text_has=[('**/web/js/output.js', 'globalThis.uxbExports["AddTwo"] = function')], out_files_absent=['**/web/browser/index.html'])
case('host_import_wat_import_and_page_table', '%%HOST_IMPORT env.log AS host_log SIG "VOID(I32)"\nPRINT 1\n', verb=BROWSER_WAT,
     out_text_has=[('**/web/wasm/output.wat', '(import "env" "log" (func $host_log (param i32)))'), (PAGE, 'globalThis.uxbHostImportSpec'),
                   (PAGE, '"env.log": {"alias": "host_log"'), (PAGE, 'globalThis.uxbBuildWasmImports')],
     out_json=[(MANIFEST, ['hostImports', 'env.log', 'alias'], 'host_log'), (MANIFEST, ['hostImports', 'env.log', 'signature'], 'VOID(I32)')])
case('wat_import_signature_forms',
     '%%REQUIRE_HOST_BINDING OFF\n%%WAT_IMPORT "env", "iki", "iki", "i32,i32->i32"\n%%WAT_IMPORT "env", "ham", "ham", "(param f64) (result f64)"\n'
     '%%WAT_IMPORT "env", "bos", "bos", ""\nPRINT 1\n', verb=BROWSER_WAT,
     out_text_has=[('**/web/wasm/output.wat', '(import "env" "iki" (func $iki (param i32 i32) (result i32)))'),
                   ('**/web/wasm/output.wat', '(import "env" "ham" (func $ham (param f64) (result f64)))'),
                   ('**/web/wasm/output.wat', '(import "env" "bos" (func $bos))')])
case('wat_func_and_export_enter_the_module',
     '%%ALLOW_RAW_WAT ON\n%%WAT_FUNC_BEGIN yardimci\n(func $twice (param i32) (result i32) (i32.mul (local.get 0) (i32.const 2)))\n%%WAT_FUNC_END\n%%WAT_EXPORT twice\nPRINT 1\n',
     verb=BROWSER_WAT,
     out_text_has=[('**/web/wasm/output.wat', '(func $twice (param i32) (result i32) (i32.mul (local.get 0) (i32.const 2)))'),
                   ('**/web/wasm/output.wat', '(export "twice" (func $twice))')], wat2wasm=['**/web/wasm/output.wat'])

# gen blocks inside the browser package
case('gen_block_lands_in_the_package', '%%GEN_BLOCK "x.txt"\nicerik\n%%GEN_END\nPRINT 1\n', verb=BROWSER,
     out_files=[('**/web/generated/x.txt', None)], out_files_absent=['x.txt'])

# native x64 only: the stack contents of a local that is not cleared (NOZEROVARS) and the wipe on return (SECSTACK)
STALE = ('FUNCTION Tekrar(n AS I64) AS I64\n    DIM x AS I64\n    DIM r AS I64\n    r = x\n    x = n\n    RETURN r\nEND FUNCTION\n'
         'DIM a AS I64\nDIM b AS I64\na = Tekrar(5)\nb = Tekrar(9)\nPRINT b\n')
case('nozerovars_off_clears_locals', STALE, native=[('MIR-x64', '0'), ('AST-x64', '0')], interp=[('AST', '0'), ('MIR', '0')])
case('nozerovars_on_keeps_the_stack_value', '%%NOZEROVARS ON\n' + STALE, native=[('MIR-x64', '5'), ('AST-x64', '5')], interp=[('AST', '0'), ('MIR', '0')],
     web=[('JS', '0'), ('WASM', '0')])
case('nozerovars_explicit_initial_value_still_applies',
     '%%NOZEROVARS ON\nFUNCTION Tekrar(n AS I64) AS I64\n    DIM x AS I64 = 3\n    DIM r AS I64\n    r = x\n    x = n\n    RETURN r\nEND FUNCTION\n'
     'DIM a AS I64\nDIM b AS I64\na = Tekrar(5)\nb = Tekrar(9)\nPRINT b\n', native=[('MIR-x64', '3'), ('AST-x64', '3')], interp=[('AST', '3'), ('MIR', '3')])
case('nozerovars_off_switches_it_back', '%%NOZEROVARS ON\n%%NOZEROVARS OFF\n' + STALE, native=[('MIR-x64', '0'), ('AST-x64', '0')])
case('secstack_wipes_the_frame_on_return', '%%NOZEROVARS ON\n%%SECSTACK ON\n' + STALE, native=[('MIR-x64', '0'), ('AST-x64', '0')], interp=[('AST', '0'), ('MIR', '0')])
case('secstack_alone_keeps_results', '%%SECSTACK ON\nFUNCTION Sq(n AS I64) AS I64\n    DIM r AS I64\n    r = n * n\n    RETURN r\nEND FUNCTION\nPRINT Sq(12)\nPRINT Sq(7)\n',
     native=[('MIR-x64', '144\n49'), ('AST-x64', '144\n49')], interp=[('AST', '144\n49'), ('MIR', '144\n49')])

CASE_COUNT = len(CASES)


def run_case(compiler, work, spec):
    source = work / 'program.uxb'
    source.write_text(spec['source'], encoding='utf-8')
    for rel, data in spec['files'].items():
        target = work / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    expanded = work / 'expanded.uxb'
    pr_json = work / 'pr.json'
    out_root = work / 'out'
    command = [str(compiler)] + spec['verb'] + [str(source), '--out-root', str(out_root), '--preprocessed-out', str(expanded),
                                                '--preprocess-result-json-out', str(pr_json)] + spec['args']
    p = subprocess.run(command, cwd=work, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180)
    (work / 'stdout.txt').write_text(p.stdout, encoding='utf-8')
    (work / 'stderr.txt').write_text(p.stderr, encoding='utf-8')
    text = p.stdout + p.stderr
    expect = spec['expect']
    checks = {}
    if 'error' in expect:
        checks['rejected'] = p.returncode != 0
        checks['diagnostic'] = expect['error'] in text
    else:
        checks['exit_zero'] = p.returncode == 0
    for needle in expect.get('out_has', []):
        checks['out_has:' + needle] = needle in text
    for needle in expect.get('out_lacks', []):
        checks['out_lacks:' + needle] = needle not in text
    if 'expanded' in expect:
        got = expanded.read_text(encoding='utf-8-sig').strip() if expanded.exists() else None
        checks['expanded'] = got == expect['expanded']
    for needle in expect.get('expanded_has', []):
        got = expanded.read_text(encoding='utf-8-sig') if expanded.exists() else ''
        checks['expanded_has:' + needle] = needle in got
    for jname, path, want in expect.get('json', []):
        try:
            node = json.loads((work / jname).read_text(encoding='utf-8-sig'))
            for key in path:
                node = node[key]
            checks['json:%s=%s' % ('.'.join(map(str, path)), want)] = node == want
        except (OSError, ValueError, KeyError, IndexError, TypeError):
            checks['json:%s=%s' % ('.'.join(map(str, path)), want)] = False
    for pattern, want in expect.get('out_files', []):
        found = rel_matches(out_root, pattern)
        ok = len(found) >= 1
        if ok and want is not None:
            ok = found[0].read_bytes() == want
        checks['file:' + pattern] = ok
    for pattern in expect.get('out_files_absent', []):
        checks['file_absent:' + pattern] = len(rel_matches(out_root, pattern)) == 0
    for rel, want in expect.get('cwd_files', []):
        # files below the working folder (the compile runs inside the case's private folder)
        target = work / rel
        checks['cwd_file:' + rel] = target.exists() and (want is None or target.read_bytes() == want)
    for pattern, needle in expect.get('out_text_has', []):
        found = rel_matches(out_root, pattern)
        text = found[0].read_text(encoding='utf-8', errors='replace') if found else ''
        checks['text_has:%s:%s' % (pattern, needle)] = needle in text
    for pattern, needle in expect.get('out_text_lacks', []):
        found = rel_matches(out_root, pattern)
        text = found[0].read_text(encoding='utf-8', errors='replace') if found else None
        checks['text_lacks:%s:%s' % (pattern, needle)] = text is not None and needle not in text
    for pattern, path, want in expect.get('out_json', []):
        label = 'out_json:%s:%s=%s' % (pattern, '.'.join(map(str, path)), want)
        try:
            found = rel_matches(out_root, pattern)
            node = json.loads(found[0].read_text(encoding='utf-8-sig'))
            for key in path:
                node = node[key]
            checks[label] = node == want
        except (IndexError, OSError, ValueError, KeyError, TypeError):
            checks[label] = False
    for pattern in expect.get('node_check', []):
        found = rel_matches(out_root, pattern)
        if NODE is None:
            checks['node_check:' + pattern] = True  # no node on this machine: the textual checks above still apply
        else:
            r = subprocess.run([NODE, '--check', str(found[0])], capture_output=True, text=True, timeout=60) if found else None
            checks['node_check:' + pattern] = r is not None and r.returncode == 0
    for pattern in expect.get('wat2wasm', []):
        found = rel_matches(out_root, pattern)
        if not WAT2WASM.exists():
            checks['wat2wasm:' + pattern] = True  # wabt is not installed here: the textual checks above still apply
        else:
            r = subprocess.run([str(WAT2WASM), str(found[0]), '-o', str(work / 'check.wasm')], capture_output=True, text=True, timeout=60) if found else None
            checks['wat2wasm:' + pattern] = r is not None and r.returncode == 0
    for mode, want in expect.get('native', []):
        # native x64 (MIR-x64 default, or the legacy AST-x64): build, run the program, compare its output
        build = [str(compiler), 'bld', str(source)] + (['--x64-mode', 'AST'] if mode == 'AST-x64' else [])
        pb = subprocess.run(build, cwd=work, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=240)
        found = re.search(r'build tamamlandi: (\S+)', pb.stdout + pb.stderr)
        got = None
        if found:
            exe = Path(found.group(1))
            exe = exe if exe.is_absolute() else work / exe
            pr = subprocess.run([str(exe)], cwd=work, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
            got = '\n'.join(ln for ln in (pr.stdout + pr.stderr).splitlines() if ln.strip() and not ln.startswith(('INFO', 'WARN'))).strip()
        checks['native:%s' % mode] = got == want
    for mode, want in expect.get('web', []):
        # JS runs the generated file with node; WASM builds the module with wat2wasm and runs the generated runner with node
        got = None
        if mode == 'JS' and NODE is not None:
            js = work / 'p.js'
            subprocess.run([str(compiler), 'jsw', str(source), '--js-out', str(js)], cwd=work, capture_output=True, text=True, timeout=120)
            if js.exists():
                pr = subprocess.run([NODE, str(js)], cwd=work, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
                got = '\n'.join(ln for ln in (pr.stdout + pr.stderr).splitlines() if ln.strip() and not ln.startswith(('INFO', 'WARN'))).strip()
        elif mode == 'WASM' and NODE is not None and WAT2WASM.exists():
            wd = work / 'wasm'
            wd.mkdir(exist_ok=True)
            subprocess.run([str(compiler), 'wat', str(source), '--emit-wasm', '--wasm-out', str(wd / 'p.wasm'), '--wat-out', str(wd / 'p.wat'),
                            '--wat2wasm=' + str(WAT2WASM)], cwd=work, capture_output=True, text=True, timeout=120)
            if (wd / 'p.wasm').exists() and (wd / 'run_wasm.js').exists():
                pr = subprocess.run([NODE, str(wd / 'run_wasm.js')], cwd=work, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
                got = '\n'.join(ln for ln in (pr.stdout + pr.stderr).splitlines() if ln.strip() and not ln.startswith(('INFO', 'WARN'))).strip()
        else:
            checks['web:%s' % mode] = True  # node / wabt missing on this machine
            continue
        checks['web:%s' % mode] = got == want
    for mode, want in expect.get('interp', []):
        run = [str(compiler), 'run', str(source)] + (['--interpreter-backend', 'MIR'] if mode == 'MIR' else [])
        pr = subprocess.run(run, cwd=work, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=120)
        got = '\n'.join(ln for ln in (pr.stdout + pr.stderr).splitlines() if ln.strip() and not ln.startswith(('INFO', 'WARN'))).strip()
        checks['interp:%s' % mode] = got == want
    return p, command, checks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--uxb', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--only', default='', help='run only cases whose name contains this text')
    args = parser.parse_args()
    compiler = Path(args.uxb).resolve()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for spec in CASES:
        if args.only and args.only not in spec['name']:
            continue
        work = output / spec['name']
        work.mkdir()
        with tempfile.TemporaryDirectory(prefix='uxb_pp_effects_') as scratch:
            # run inside a private directory so nothing leaks into the repository; copy results back for inspection
            scratch_path = Path(scratch)
            p, command, checks = run_case(compiler, scratch_path, spec)
            passed = all(checks.values())
            if not passed:
                for item in scratch_path.rglob('*'):
                    if item.is_file() and item.stat().st_size < 262144:
                        dest = work / item.relative_to(scratch_path)
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes(item.read_bytes())
            rows.append(dict(name=spec['name'], passed=passed, checks=checks, exit=p.returncode, command=command))
            print(('PASS ' if passed else 'FAIL ') + spec['name'], flush=True)
            if not passed:
                for key, ok in checks.items():
                    if not ok:
                        print('   eksik: ' + key, flush=True)
    summary = dict(compiler=str(compiler), compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),
                   total=len(rows), passed=sum(r['passed'] for r in rows), results=rows)
    (output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    passed = sum(r['passed'] for r in rows)
    print('Toplam: %d PASS: %d FAIL: %d' % (len(rows), passed, len(rows) - passed), flush=True)
    return int(passed != len(rows))


if __name__ == '__main__':
    raise SystemExit(main())
