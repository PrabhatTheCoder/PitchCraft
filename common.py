import logging
import os
import sys
from django.apps import apps
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import inspect
from rest_framework.pagination import PageNumberPagination


logger = logging.getLogger(__name__)

ERROR_MSG = "Something went wrong, please try again later!"
APP_NAME = "base_app"


def _get_caller_info(skip=2):
    """
    Returns full file path and line number of caller.
    skip=2 means:
        0 = this function
        1 = log wrapper
        2 = actual caller
    """
    try:
        frame = inspect.stack()[skip]
        full_path = os.path.abspath(frame.filename)
        line = frame.lineno
        return full_path, line
    except Exception:
        return "unknown", "unknown"

def handle_error_log(e, view_name, app_name, extra_values=None):
    try:
        # Try to extract traceback info first
        exc_type, exc_obj, exc_tb = sys.exc_info()

        if exc_tb is not None:
            full_path = os.path.abspath(exc_tb.tb_frame.f_code.co_filename)
            line = exc_tb.tb_lineno
        else:
            # No traceback (can happen in signal handlers)
            full_path, line = _get_caller_info(skip=2)

        logger.error(
            f"Error | File: {full_path} | "
            f"Line: {line} | "
            f"View: {view_name} | "
            f"Error: {str(e)} | "
            f"Extra: {extra_values}",
            extra={"AppName": app_name},
            exc_info=True,   # ⭐ Proper stacktrace logging
        )

    except Exception as log_error:
        print("LOGGER FAILURE:", log_error)

def handle_info_log(msg, view_name, app_name, extra_values=None):
    try:
        full_path, line = _get_caller_info(skip=2)

        logger.info(
            f"Info | File: {full_path} | "
            f"Line: {line} | "
            f"View: {view_name} | "
            f"Message: {msg} | "
            f"Extra: {extra_values}",
            extra={"AppName": app_name},
        )

    except Exception as log_error:
        print("LOGGER FAILURE:", log_error)


def encrypt_sensitive_data(plaintext: str, key: bytes, iv: bytes) -> str:
    try:
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # Pad plaintext to 16 bytes
        pad_len = 16 - len(plaintext) % 16
        padded = plaintext + chr(pad_len) * pad_len

        ct = encryptor.update(padded.encode()) + encryptor.finalize()
        return base64.b64encode(ct).decode('utf-8')
    except Exception as e:
        handle_error_log(e=e, view_name=inspect.currentframe().f_code.co_name, app_name=APP_NAME)

class CustomPageNumberPagination(PageNumberPagination):
    """ 
        Override the pagination class for dynamic pagination. 
        Functionality to dynamically set the page size as a query parameter.
    """

    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 50


SUBSCRIPTION_VERSION_KEY = "subscription:version:{user_id}"