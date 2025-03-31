import nacl.public
import base64


def encrypt_to_b64(message: str) -> str:
    """
    Encrypts a message using the server's public key and the client's private key.

    Args:
        message (str): The message to be encrypted.

    Returns:
        str: The encrypted message in base64 encoding.
    """

    # Read the server's public key
    with open(".server_public_key.bin", "rb") as f:
        server_pub_key_bytes = f.read()

    # Convert the server's public key to a public key object
    server_pub_key = nacl.public.PublicKey(server_pub_key_bytes)

    # Read the client's private key
    with open(".client_private_key.bin", "rb") as f:
        client_private_key_bytes = f.read()

    # Convert the client's private key to a private key object
    client_priv_key = nacl.public.PrivateKey(client_private_key_bytes)

    # Create a box object using the client's private key and the server's public key
    box = nacl.public.Box(client_priv_key, server_pub_key)

    # Encrypt the message
    encrypted = box.encrypt(message.encode())

    # Encode the encrypted message to base64
    encrypted_b64 = base64.b64encode(encrypted).decode("utf-8")

    # Return the encrypted message in base64 encoding
    return encrypted_b64
