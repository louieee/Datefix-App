
def get_key(name):
    """
    This function returns a secret key to be used for encryption based on the name
    :param name: The name comprises of the names of the two users in a chat session
    :return:
    """
    import os
    salt = os.urandom(16)
    name = name.encode()
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(),
                     length=32,
                     salt=salt,
                     iterations=100000,
                     backend=default_backend())
    import base64
    key = base64.urlsafe_b64encode(kdf.derive(name))
    return key
