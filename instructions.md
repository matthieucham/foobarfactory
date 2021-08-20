# Foobartory Back

# Foobartory

## Avant-propos

- Utilise le langage de ton choix
- Un output console est suffisant
- Envoies ta réponse sous la forme d'un repo Github que nous pouvons `git clone` avec un readme expliquant comment le faire fonctionner et tes remarques sur ton travail.
- Nous cherchons à comprendre comment tu codes et comment tu appréhendes une question ouverte.
- N'hésite pas à nous contacter matthieu@getalma.eu si tu as des questions.
- Le projet est pensé pour durer environ 3 heures. Nous sommes conscients que tu as d'autres obligations, et nous ne te demandons donc pas la "réponse parfaite".

## Enoncé

Le but est de coder une chaîne de production automatique de `foobar`.

On dispose au départ de 2 robots, mais on souhaite accélérer la production pour prendre le contrôle du marché des `foobar`. Pour ce faire on va devoir acheter davantage de robots, le programme s'arrête quand on a 30 robots.

Les robots sont chacun capables d'effectuer les activités suivantes :

- Miner du `foo` : occupe le robot pendant 1 seconde.
- Miner du `bar` : occupe le robot pendant un temps aléatoire compris entre 0.5 et 2 secondes.
- Assembler un `foobar` à partir d'un `foo` et d'un `bar` : occupe le robot pendant 2 secondes. L'opération a 60% de chances de succès ; en cas d'échec le `bar` peut être réutilisé, le `foo` est perdu.
- Vendre des `foobar` : 10s pour vendre de 1 à 5 foobar, on gagne 1€ par foobar vendu
- Acheter un nouveau robot pour 3€ et 6 `foo`, 0s

A chaque changement de type d'activité, le robot doit se déplacer à un nouveau poste de travail, cela l'occupe pendant 5s.

Notes:

- 1 seconde du jeu n'a pas besoin d'être une seconde réelle.
- Le choix des activités n'a *pas besoin d'être optimal* (pas besoin de faire des maths), seulement fonctionnel.