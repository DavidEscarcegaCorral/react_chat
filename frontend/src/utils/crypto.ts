function arrayBufferToBase64(bytes: Uint8Array): string {
  let binary = '';
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

async function importPublicKey(pem: string): Promise<CryptoKey> {
  const pemHeader = '-----BEGIN PUBLIC KEY-----';
  const pemFooter = '-----END PUBLIC KEY-----';
  const pemContents = pem.substring(pemHeader.length, pem.indexOf(pemFooter)).replace(/\r?\n/g, '');

  const binaryDer = Uint8Array.from(atob(pemContents), (c) => c.charCodeAt(0));

  return await crypto.subtle.importKey(
    'spki',
    binaryDer.buffer,
    { name: 'RSA-OAEP', hash: 'SHA-256' },
    false,
    ['encrypt'],
  );
}

export async function encryptMessage(plaintext: string, publicKeyPem: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(plaintext);

  const aesKey = crypto.getRandomValues(new Uint8Array(16));
  const iv = crypto.getRandomValues(new Uint8Array(16));

  const aesCryptoKey = await crypto.subtle.importKey(
    'raw', aesKey, { name: 'AES-CBC' }, false, ['encrypt'],
  );
  const encryptedMsg = await crypto.subtle.encrypt(
    { name: 'AES-CBC', iv }, aesCryptoKey, data,
  );

  const publicKey = await importPublicKey(publicKeyPem);
  const keyIv = new Uint8Array(aesKey.length + iv.length);
  keyIv.set(aesKey);
  keyIv.set(iv, aesKey.length);
  const encryptedKey = await crypto.subtle.encrypt(
    { name: 'RSA-OAEP' }, publicKey, keyIv,
  );

  const encryptedKeyBytes = new Uint8Array(encryptedKey);
  const encryptedMsgBytes = new Uint8Array(encryptedMsg);

  const keyB64 = arrayBufferToBase64(encryptedKeyBytes);
  const msgB64 = arrayBufferToBase64(encryptedMsgBytes);

  return `${keyB64}|${msgB64}`;
}
