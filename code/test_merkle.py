from binascii import hexlify
from merkle import SaltedMerkle
from os import urandom


def test_merkle():
    n = 64
    elements = [urandom(int(urandom(1)[0])) for i in range(n)]
    tree = SaltedMerkle(elements)
    root = tree.root()

    # opening any leaf should work
    for i in range(n):
        salt, path = tree.open(i)
        assert(SaltedMerkle.verify(root, i, salt, path, elements[i]))

    # opening non-leafs should not work
    for i in range(n):
        salt, path = tree.open(i)
        assert(False == SaltedMerkle.verify(root, i, salt, path, urandom(51)))

    # opening wrong leafs should not work
    for i in range(n):
        salt, path = tree.open(i)
        j = (i + 1 + (int(urandom(1)[0] % (n-1)))) % n
        assert(False == SaltedMerkle.verify(root, i, salt, path, elements[j]))

    # opening leafs with the wrong index should not work
    for i in range(n):
        salt, path = tree.open(i)
        j = (i + 1 + (int(urandom(1)[0] % (n-1)))) % n
        assert(False == SaltedMerkle.verify(root, j, salt, path, elements[i]))

    # opening leafs to a false root should not work
    for i in range(n):
        salt, path = tree.open(i)
        assert(False == SaltedMerkle.verify(
            urandom(32), i, salt, path, elements[i]))

    # opening leafs with even one falsehood in the path should not work
    for i in range(n):
        salt, path = tree.open(i)
        for j in range(len(path)):
            fake_path = path[0:j] + [urandom(32)] + path[j+1:]
            assert(False == SaltedMerkle.verify(
                root, i, salt, fake_path, elements[i]))

    # opening leafs with false salt should not work
    for i in range(n):
        salt, path = tree.open(i)
        assert(False == SaltedMerkle.verify(
            root, i, urandom(32), path, elements[i]))
