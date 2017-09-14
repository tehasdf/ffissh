from . import constants, exceptions


def _run_until_done(func, *args, **kwargs):
    """Keep retrying func(*args, **kwargs) if it returns EAGAIN.

    Raise a RuntimeError if it returns nonzero.
    This is a common idiom in the library. However, it is mostly useful with
    nonblocking sessions which we don't actually use here, so perhaps
    the EAGAIN checking isn't required after all.
    """
    while True:
        rc = func(*args, **kwargs)
        if rc != constants.LIBSSH2_ERROR_EAGAIN:
            break
    if rc:
        raise exceptions.SSHError(
            'Error calling {func}(*{args}, **{kwargs})'.format(
                func=func,
                args=args,
                kwargs=kwargs,
                ),
            rc)
