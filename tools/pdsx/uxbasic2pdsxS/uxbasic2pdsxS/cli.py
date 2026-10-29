from __future__ import annotations

from pathlib import Path
import argparse
import sys

from .loader import load_ast, load_optional_json, diagnostics_have_errors, extract_profile_from_preprocess_result, BridgeLoadError
from .source_model import SourceModel
from .emitter import PdsxEmitter
from .project_writer import write_project, write_report, write_usage_doc


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="uxbasic2pdsxS",
        description="uXBasic JSON klasöründen pdsX BASX/proje düzeni üretir.",
    )
    p.add_argument("--json-dir", required=True, help="uXBasic'in tüm JSON çıktılarının bulunduğu klasör")
    p.add_argument("--ast-json", default="", help="Varsayılan yerine kullanılacak AST JSON dosyası")
    p.add_argument("--source", default="", help="Yorumları aynen taşımak için kaynak veya preprocessed uXBasic dosyası")
    p.add_argument("--out", required=True, help="Üretilecek pdsX proje klasörü")
    p.add_argument("--project-name", default="uxb_generated", help="pdsX proje adı")
    p.add_argument("--profile", default="", help="pdsX profile adı; örn. py30_std, py30_thirdparty, ai_pack")
    p.add_argument("--profiles-dir", default="profiles/", help="project.prj içine yazılacak profiles yolu")
    p.add_argument("--headers-dir", default="hx/", help="project.prj içine yazılacak hx/headers yolu")
    p.add_argument("--copy-profiles-from", default="", help="Hazır profiles klasörünü çıktı içine kopyala")
    p.add_argument("--copy-hx-from", default="", help="Hazır hx klasörünü çıktı içine kopyala")
    p.add_argument("--requirement", action="append", default=[], help="project.prj [requirements] package satırı; birden çok verilebilir")
    p.add_argument("--strict-diagnostics", action="store_true", help="lexer/parser diagnostics JSON hata içerirse dur")
    p.add_argument("--strict-coverage", action="store_true", help="AST node kapsam raporunda işlenmemiş node varsa hata kodu 30 ile dur")
    p.add_argument("--no-profile-line", action="store_true", help="main.basx başına PROFILE satırı yazma")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    json_dir = Path(args.json_dir).resolve()
    out_dir = Path(args.out).resolve()
    ast_path = Path(args.ast_json).resolve() if args.ast_json else None
    source_path = Path(args.source).resolve() if args.source else None

    try:
        if args.strict_diagnostics:
            lex_diag = load_optional_json(json_dir, ["lexer_diagnostics.json", "lex_diagnostics.json"])
            par_diag = load_optional_json(json_dir, ["parser_diagnostics.json", "parse_diagnostics.json"])
            if diagnostics_have_errors(lex_diag) or diagnostics_have_errors(par_diag):
                print("uxbasic2pdsxS: lexer/parser diagnostics hata içeriyor; üretim durduruldu.", file=sys.stderr)
                return 20

        root = load_ast(json_dir, ast_path)
        source = SourceModel.discover(json_dir, source_path)
        profile = args.profile
        if not profile:
            preprocess_json = load_optional_json(json_dir, ["preprocess_result.json", "preprocess.json", "preprocessor_result.json"])
            profile = extract_profile_from_preprocess_result(preprocess_json)
        emitter = PdsxEmitter(source=source, profile=profile, keep_profile_line=not args.no_profile_line)
        basx_text, report = emitter.convert(root)
        if args.strict_coverage and sum(report.unhandled_counts.values()) > 0:
            print("uxbasic2pdsxS: AST node kapsamı eksik; üretim durduruldu.", file=sys.stderr)
            return 30

        project_info = write_project(
            out_dir=out_dir,
            project_name=args.project_name,
            basx_text=basx_text,
            profile=profile,
            profiles_dir=args.profiles_dir,
            headers_dir=args.headers_dir,
            requirements=args.requirement,
            copy_profiles_from=Path(args.copy_profiles_from).resolve() if args.copy_profiles_from else None,
            copy_hx_from=Path(args.copy_hx_from).resolve() if args.copy_hx_from else None,
        )
        write_report(out_dir, report, project_info)
        write_usage_doc(out_dir, project_info)

        print("uxbasic2pdsxS: OK")
        print(f"  project : {project_info['project']}")
        print(f"  basx    : {project_info['basx']}")
        print(f"  report  : {project_info['reports']}/uxbasic2pdsxS_report.json")
        return 0
    except BridgeLoadError as exc:
        print(f"uxbasic2pdsxS: HATA: {exc}", file=sys.stderr)
        return 10
    except Exception as exc:
        print(f"uxbasic2pdsxS: BEKLENMEYEN HATA: {exc}", file=sys.stderr)
        return 99


if __name__ == "__main__":
    raise SystemExit(main())
