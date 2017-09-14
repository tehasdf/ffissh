# file "example_build.py"

# Note: we instantiate the same 'cffi.FFI' class as in the previous
# example, but call the result 'ffibuilder' now instead of 'ffi';
# this is to avoid confusion with the other 'ffi' object you get below

from cffi import FFI

ffibuilder = FFI()

ffibuilder.set_source(
    "ffissh._libssh2",
    r""" // passed to the real C compiler
        #include "libssh2.h"
        #include "libssh2_sftp.h"
    """,
    libraries=[
        "ssh2",
        ],
    )

# those are just mostly copied from libssh2.h
ffibuilder.cdef("""
typedef struct _LIBSSH2_SESSION LIBSSH2_SESSION;
typedef struct _LIBSSH2_KNOWNHOSTS LIBSSH2_KNOWNHOSTS;
typedef struct _LIBSSH2_CHANNEL LIBSSH2_CHANNEL;
typedef struct _LIBSSH2_LISTENER LIBSSH2_LISTENER;
typedef struct _LIBSSH2_SFTP LIBSSH2_SFTP;
typedef struct _LIBSSH2_SFTP_HANDLE LIBSSH2_SFTP_HANDLE;

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
ssize_t libssh2_channel_read_stderr(LIBSSH2_CHANNEL *channel,
                             char *buf, size_t buflen);

LIBSSH2_LISTENER *libssh2_channel_forward_listen(LIBSSH2_SESSION *session,
                                                 int port);
LIBSSH2_CHANNEL *libssh2_channel_forward_accept(
    LIBSSH2_LISTENER *listener);

int libssh2_session_block_directions(LIBSSH2_SESSION *session);

int libssh2_session_last_error(LIBSSH2_SESSION *session, char **errmsg,
                               int *errmsg_len, int want_buf);

int libssh2_session_last_errno(LIBSSH2_SESSION *session);

    LIBSSH2_LISTENER *libssh2_channel_forward_listen_ex(
        LIBSSH2_SESSION *session, const char *host, int port, int *bound_port,
        int queue_maxsize);

LIBSSH2_SFTP * libssh2_sftp_init(LIBSSH2_SESSION *session);

int libssh2_sftp_shutdown(LIBSSH2_SFTP *sftp);

LIBSSH2_SFTP_HANDLE * libssh2_sftp_open(
        LIBSSH2_SFTP *sftp, const char *path, unsigned long flags, long mode);

int libssh2_sftp_close_handle(LIBSSH2_SFTP_HANDLE *handle);

ssize_t libssh2_sftp_read(
        LIBSSH2_SFTP_HANDLE *handle, char *buffer, size_t buffer_maxlen);
ssize_t libssh2_sftp_write(LIBSSH2_SFTP_HANDLE *handle, const char *buffer,
                           size_t count);
ssize_t libssh2_channel_write(LIBSSH2_CHANNEL *channel, const char *buf,
                                             size_t buflen);

""")

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
