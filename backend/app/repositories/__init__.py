"""Package « repositories » : accès aux données.

Les routes de l'API ne manipulent JAMAIS la base directement : elles
passent par un « dépôt » (repository). Depuis l'Étape 4, les dépôts
SQL (dossier sql/) lisent et écrivent dans PostgreSQL.
Les conversions de lignes SQL → dictionnaires API sont dans
serializers.py (un seul endroit à modifier si un champ est ajouté).
"""
