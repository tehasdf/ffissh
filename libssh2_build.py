# file "example_build.py"

# Note: we instantiate the same 'cffi.FFI' class as in the previous
# example, but call the result 'ffibuilder' now instead of 'ffi';
# this is to avoid confusion with the other 'ffi' object you get below

from cffi import FFI

ffibuilder = FFI()

ffibuilder.set_source(
    "_libssh2_py",
    r""" // passed to the real C compiler
        #include "libssh2.h"
    """,
    libraries=[])

# those are just mostly copied from libssh2.h
ffibuilder.cdef("""
    typedef struct _LIBSSH2_SESSION LIBSSH2_SESSION;
    typedef struct _LIBSSH2_KNOWNHOSTS LIBSSH2_KNOWNHOSTS;
    typedef struct _LIBSSH2_CHANNEL LIBSSH2_CHANNEL;
    struct libssh2_knownhost {
        unsigned int magic;  /* magic stored by the library */
        void *node; /* handle to the internal representation of this host */
        char *name; /* this is NULL if no plain text host name exists */
        char *key;  /* key in base64/printable format */
        int typemask;
    };
    void libssh2_session_set_blocking(LIBSSH2_SESSION *session, int blocking);
    LIBSSH2_SESSION * libssh2_session_init();
    int libssh2_session_handshake(LIBSSH2_SESSION *session, int sock);
    LIBSSH2_KNOWNHOSTS * libssh2_knownhost_init(LIBSSH2_SESSION *session);
    int libssh2_knownhost_readfile(LIBSSH2_KNOWNHOSTS *hosts,
                                  const char *filename, int type);
    int libssh2_knownhost_writefile(LIBSSH2_KNOWNHOSTS *hosts,
                                   const char *filename, int type);
    const char *libssh2_session_hostkey(LIBSSH2_SESSION *session,
                                        size_t *len, int *type);
    int libssh2_knownhost_checkp(LIBSSH2_KNOWNHOSTS *hosts,
                         const char *host, int port,
                         const char *key, size_t keylen,
                         int typemask,
                         struct libssh2_knownhost **knownhost);
    void libssh2_knownhost_free(LIBSSH2_KNOWNHOSTS *hosts);
    int libssh2_userauth_publickey_fromfile(
        LIBSSH2_SESSION *session,
        const char *username,
        const char *publickey,
        const char *privatekey,
        const char *passphrase);
    LIBSSH2_CHANNEL *libssh2_channel_open_session(LIBSSH2_SESSION *session);
    int libssh2_channel_exec(LIBSSH2_CHANNEL *channel, const char *command);
    ssize_t libssh2_channel_read(LIBSSH2_CHANNEL *channel,
                                 char *buf, size_t buflen);
""")

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
