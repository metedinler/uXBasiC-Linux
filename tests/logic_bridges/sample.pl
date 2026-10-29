parent(ali, veli).
parent(veli, ayse).
ancestor(X, Y) :- parent(X, Y).
ancestor(X, Y) :- parent(X, Z), ancestor(Z, Y).

fuzzy_hot(Temperature, Membership) :-
    Membership is max(0.0, min(1.0, (Temperature - 20.0) / 10.0)).

print_ancestor :-
    (ancestor(ali, ayse) -> writeln('PROLOG_ANCESTOR=1'); writeln('PROLOG_ANCESTOR=0')).

print_fuzzy :-
    fuzzy_hot(25.0, M),
    format('FUZZY_PROLOG=~2f~n', [M]).
