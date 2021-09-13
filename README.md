# foobarfactory

Implémentation de l'exercice de programmation suivant. Le jeu a été réalisé en `python`, testé sur les versions `3.6, 3.7, 3.8, 3.9`.

## Enoncé
> 
> Le but est de coder une chaîne de production automatique de `foobar`.
> 
> On dispose au départ de 2 robots, mais on souhaite accélérer la production pour prendre le contrôle du marché des `foobar`. Pour ce faire on va devoir acheter davantage de robots, le programme s'arrête quand on a 30 robots.
> 
> Les robots sont chacun capables d'effectuer les activités suivantes :
> 
> - Miner du `foo` : occupe le robot pendant 1 seconde.
> - Miner du `bar` : occupe le robot pendant un temps aléatoire compris entre 0.5 et 2 secondes.
> - Assembler un `foobar` à partir d'un `foo` et d'un `bar` : occupe le robot pendant 2 secondes. L'opération a 60% de chances de succès ; en cas d'échec le `bar` peut être réutilisé, le `foo` est perdu.
> - Vendre des `foobar` : 10s pour vendre de 1 à 5 foobar, on gagne 1€ par foobar vendu
> - Acheter un nouveau robot pour 3€ et 6 `foo`, 0s
> 
> A chaque changement de type d'activité, le robot doit se déplacer à un nouveau poste de travail, cela l'occupe pendant 5s.


## Comment jouer ?

### Installation

- **Sur runtime python local**

Installer les dépendances dans l'environnement python. L'utilisation d'un virtualenv est recommandée.

```shell
pip install -r requirements.txt
```

Le seul module installé est `click` : https://palletsprojects.com/p/click/

- **Dans un container Docker**

Construire l'image docker du projet

```shell
docker build -t foobarfactory . 
```

### Utilisation

Le but du jeu est d'atteindre les 30 robots. Le jeu offre 2 modes pour celà : 
- le mode automatique : c'est la machine qui joue et qui prend les décisions pour atteindre l'objectif
- le mode interactif : c'est le joueur humain qui prend les décisions

Pour lancer le jeu en mode automatique (par défaut) il suffit de lancer le script sans options:

**Runtime local**

```shell
python src/foobarfactory.py
```

**Docker**

```shell
docker run -i foobarfactory foobarfactory.py
```

Par défaut les pas de temps de l'usine durent une vraie seconde. Mais il est possible d'accélérer, avec des pas de temps simulés:

```shell
python src/foobarfactory.py --delay 0
```

```shell
docker run -i foobarfactory foobarfactory.py --delay 0
```

En mode automatique, la machine arrive à atteindre les 30 robots en 400 à 500 pas de temps. Pouvez-vous faire mieux ? Pour le savoir, jouez en mode interactif :

```shell
python src/foobarfactory.py --delay 0 --pilot interactive
```

```shell
docker run -i foobarfactory foobarfactory.py --delay 0 --pilot interactive
```
*Attention à ne pas oublier le flag `-i` pour que le container accepte d'attendre les commandes entrées par la console.*

A chaque fois que des robots sont disponibles, vous devez indiquer quelle devra être leur prochaine activité, en entrant la lettre correspondant à l'action voulue (lettre entre parenthèses dans la liste des actions). Seules les actions possibles sont proposées.

Pas facile ? Dans ce cas mesurez-vous à la stratégie "dumb" de la machine, qui atteint l'objectif en 700 à 800 pas de temps:

```shell
python src/foobarfactory.py --delay 0 --pilot dumb
```

```shell
docker run -i foobarfactory foobarfactory.py --delay 0 --pilot dumb
```


## Considérations techniques

### Structure du projet

```
src/                Contient le script python principal foobarfactory.py                 
├── model           Module définissant le "modèle physique" de la foobarfactory
```

### Tests unitaires

Seul le module du modèle physique comporte des tests unitaires. Pour les exécuter, installez `pytest` puis

```shell
pytest
```
