import base64 as b,getpass as g,urllib.parse as u
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt as K
from cryptography.hazmat.primitives.ciphers.aead import AESGCM as A
i=input("Encrypted: ");i=u.unquote(i);i=i[i.find("#")+1:]if"#"in i else i
x=b.urlsafe_b64decode(i);p=g.getpass("Password: ")
k=K(salt=x[4:20],length=32,n=1<<x[1],r=x[2],p=x[3]).derive(p.encode())
print(A(k).decrypt(x[20:32],x[32:],x[:32]).decode())
