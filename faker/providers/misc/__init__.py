# coding=utf-8

from __future__ import unicode_literals
import hashlib
import io
import string
import tarfile
import uuid
import sys
import zipfile

import six

from .. import BaseProvider


localized = True


class Provider(BaseProvider):
    def boolean(self, chance_of_getting_true=50):
        return self.generator.random.randint(1, 100) <= chance_of_getting_true

    def null_boolean(self):
        return {
            0: None,
            1: True,
            -1: False,
        }[self.generator.random.randint(-1, 1)]

    def binary(self, length=(1 * 1024 * 1024)):
        """ Returns random binary blob.

        Default blob size is 1 Mb.
        """
        blob = [self.generator.random.randrange(256) for _ in range(length)]
        return bytes(blob) if sys.version_info[0] >= 3 else bytearray(blob)

    def md5(self, raw_output=False):
        """
        Calculates the md5 hash of a given string
        :example 'cfcd208495d565ef66e7dff9f98764da'
        """
        res = hashlib.md5(str(self.generator.random.random()).encode('utf-8'))
        if raw_output:
            return res.digest()
        return res.hexdigest()

    def sha1(self, raw_output=False):
        """
        Calculates the sha1 hash of a given string
        :example 'b5d86317c2a144cd04d0d7c03b2b02666fafadf2'
        """
        res = hashlib.sha1(str(self.generator.random.random()).encode('utf-8'))
        if raw_output:
            return res.digest()
        return res.hexdigest()

    def sha256(self, raw_output=False):
        """
        Calculates the sha256 hash of a given string
        :example '85086017559ccc40638fcde2fecaf295e0de7ca51b7517b6aebeaaf75b4d4654'
        """
        res = hashlib.sha256(
            str(self.generator.random.random()).encode('utf-8'))
        if raw_output:
            return res.digest()
        return res.hexdigest()

    def uuid4(self, cast_to=str):
        """
        Generates a random UUID4 string.
        :param cast_to: Specify what type the UUID should be cast to. Default is `str`
        :type cast_to: callable
        """
        # Based on http://stackoverflow.com/q/41186818
        return cast_to(uuid.UUID(int=self.generator.random.getrandbits(128), version=4))

    def password(
            self,
            length=10,
            special_chars=True,
            digits=True,
            upper_case=True,
            lower_case=True):
        """
        Generates a random password.
        @param length: Integer. Length of a password
        @param special_chars: Boolean. Whether to use special characters !@#$%^&*()_+
        @param digits: Boolean. Whether to use digits
        @param upper_case: Boolean. Whether to use upper letters
        @param lower_case: Boolean. Whether to use lower letters
        @return: String. Random password
        """
        choices = ""
        required_tokens = []
        if special_chars:
            required_tokens.append(
                self.generator.random.choice("!@#$%^&*()_+"))
            choices += "!@#$%^&*()_+"
        if digits:
            required_tokens.append(self.generator.random.choice(string.digits))
            choices += string.digits
        if upper_case:
            required_tokens.append(
                self.generator.random.choice(string.ascii_uppercase))
            choices += string.ascii_uppercase
        if lower_case:
            required_tokens.append(
                self.generator.random.choice(string.ascii_lowercase))
            choices += string.ascii_lowercase

        assert len(
            required_tokens) <= length, "Required length is shorter than required characters"

        # Generate a first version of the password
        chars = self.random_choices(choices, length=length)

        # Pick some unique locations
        random_indexes = set()
        while len(random_indexes) < len(required_tokens):
            random_indexes.add(
                self.generator.random.randint(0, len(chars) - 1))

        # Replace them with the required characters
        for i, index in enumerate(random_indexes):
            chars[index] = required_tokens[i]

        return ''.join(chars)

    def zip(self, uncompressed_size=65536, num_files=1, min_file_size=4096, compression=None):
        """
        Returns a random valid zip archive

        :param uncompressed_size: Total size of files before compression, 16 KiB by default
        :param num_files: Number of files archived in resulting zip file, 1 file by default
        :param min_file_size: Minimum size of each file before compression, 4 KiB by default
        :param compression: bzip2 or bz2 for BZIP2, lzma or xz for LZMA,
                             deflate gzip or gz for GZIP, otherwise no compression

        :return: Bytes object representation of zip archive
        """

        if any([
            not isinstance(num_files, int) or num_files <= 0,
            not isinstance(min_file_size, int) or min_file_size <= 0,
            not isinstance(uncompressed_size, int) or uncompressed_size <= 0,
        ]):
            raise ValueError(
                '`num_files`, `min_file_size`, and `uncompressed_size` must be positive integers',
            )
        if min_file_size * num_files > uncompressed_size:
            raise AssertionError(
                '`uncompressed_size` is smaller than the calculated minimum required size',
            )
        if compression in ['bzip2', 'bz2']:
            if six.PY2:
                raise RuntimeError('BZIP2 compression is not supported in Python 2')
            compression = zipfile.ZIP_BZIP2
        elif compression in ['lzma', 'xz']:
            if six.PY2:
                raise RuntimeError('LZMA compression is not supported in Python 2')
            compression = zipfile.ZIP_LZMA
        elif compression in ['deflate', 'gzip', 'gz']:
            compression = zipfile.ZIP_DEFLATED
        else:
            compression = zipfile.ZIP_STORED

        zip_buffer = io.BytesIO()
        remaining_size = uncompressed_size
        with zipfile.ZipFile(zip_buffer, mode='w', compression=compression) as zip_handle:
            for file_number in range(1, num_files + 1):
                filename = self.generator.pystr() + str(file_number)

                max_allowed_size = remaining_size - (num_files - file_number) * min_file_size
                if file_number < num_files:
                    file_size = self.generator.random.randint(min_file_size, max_allowed_size)
                    remaining_size = remaining_size - file_size
                else:
                    file_size = remaining_size

                data = self.generator.binary(file_size)
                if six.PY3:
                    zip_handle.writestr(filename, data)
                else:
                    zip_handle.writestr(filename, str(data))
        return zip_buffer.getvalue()

    def tar(self, uncompressed_size=65536, num_files=1, min_file_size=4096, compression=None):
        """
        Returns a random valid tar

        :param uncompressed_size: Total size of files before compression, 16 KiB by default
        :param num_files: Number of files archived in resulting zip file, 1 file by default
        :param min_file_size: Minimum size of each file before compression, 4 KiB by default
        :param compression: gzip or gz for GZIP, bzip2 or bz2 for BZIP2,
                            lzma or xz for LZMA, otherwise no compression

        :return: Bytes object representation of tar
        """
        if any([
            not isinstance(num_files, int) or num_files <= 0,
            not isinstance(min_file_size, int) or min_file_size <= 0,
            not isinstance(uncompressed_size, int) or uncompressed_size <= 0,
        ]):
            raise ValueError(
                '`num_files`, `min_file_size`, and `uncompressed_size` must be positive integers',
            )
        if min_file_size * num_files > uncompressed_size:
            raise AssertionError(
                '`uncompressed_size` is smaller than the calculated minimum required size',
            )
        if compression in ['gzip', 'gz']:
            mode = 'w:gz'
        elif compression in ['bzip2', 'bz2']:
            mode = 'w:bz2'
        elif compression in ['lzma', 'xz']:
            if six.PY2:
                raise RuntimeError('LZMA compression is not supported in Python 2')
            mode = 'w:xz'
        else:
            mode = 'w'

        tar_buffer = io.BytesIO()
        remaining_size = uncompressed_size
        with tarfile.open(mode=mode, fileobj=tar_buffer) as tar_handle:
            for file_number in range(1, num_files + 1):
                file_buffer = io.BytesIO()
                filename = self.generator.pystr() + str(file_number)

                max_allowed_size = remaining_size - (num_files - file_number) * min_file_size
                if file_number < num_files:
                    file_size = self.generator.random.randint(min_file_size, max_allowed_size)
                    remaining_size = remaining_size - file_size
                else:
                    file_size = remaining_size

                tarinfo = tarfile.TarInfo(name=filename)
                data = self.generator.binary(file_size)
                file_buffer.write(data)
                tarinfo.size = len(file_buffer.getvalue())
                file_buffer.seek(0)
                tar_handle.addfile(tarinfo, file_buffer)
                file_buffer.close()
        return tar_buffer.getvalue()
