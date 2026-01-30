"""
Clé secrète pour la réinitialisation du mot de passe administrateur.
Cette clé doit rester confidentielle et n'est accessible qu'aux personnes
ayant accès au serveur.

Pour réinitialiser un mot de passe admin :
1. Consultez cette clé sur le serveur
2. Allez sur /administration/reset-password/
3. Entrez le nom d'utilisateur, la clé secrète et le nouveau mot de passe
"""

# Clé secrète - Changez cette valeur pour plus de sécurité
RESET_SECRET_KEY = "GiffaudAdmin2024!SecretReset"
