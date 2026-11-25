#!/usr/bin/env python3
"""Exercise the generated install and release scripts in disposable directories."""

import base64
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tempfile
import unittest


SKILL = Path(__file__).resolve().parents[1]
RELEASE = SKILL / 'templates/release/Scripts'
MAC = sys.platform == 'darwin'


class TemplateChecks(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.env = dict(os.environ, PATH=f'{self.bin}:{os.environ["PATH"]}')

    def run_command(self, *args, ok=True, **kwargs):
        result = subprocess.run(args, cwd=self.root, env=self.env, capture_output=True, text=True, **kwargs)
        self.assertEqual(result.returncode == 0, ok, f'{args}: {result.stdout}\n{result.stderr}')
        return result

    def stub(self, name, body):
        path = self.bin / name
        path.write_text('#!/bin/sh\nset -eu\n' + body + '\n')
        path.chmod(0o755)

    def test_commit_ranges(self):
        self.run_command('git', 'init', '-q')
        def commit(subject):
            self.run_command('git', '-c', 'user.name=Fixture', '-c', 'user.email=test@example.invalid',
                             '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null',
                             'commit', '-q', '--allow-empty', '-m', subject)
        commit('feat: x')
        check = RELEASE / 'check-commits.sh'
        notes = RELEASE / 'release-notes.sh'
        self.assertIn('1 commit', self.run_command('sh', check, 'HEAD^!').stdout)
        self.assertIn('0 commit', self.run_command('sh', check, 'HEAD..HEAD').stdout)
        self.assertNotIn('## Other', self.run_command('sh', notes, 'HEAD', 'HEAD', 'a/b').stdout)
        commit('fix(core): correct input')
        self.assertIn('**core:** correct input', self.run_command('sh', notes, 'HEAD~1', 'HEAD', 'a/b').stdout)
        commit('Broken subject')
        self.run_command('sh', check, 'HEAD^!', ok=False)
        self.run_command('sh', check, 'missing..HEAD', ok=False)
        for start, end in [('missing', 'HEAD'), ('HEAD', 'missing')]:
            self.assertEqual(self.run_command('sh', notes, start, end, 'a/b', ok=False).stdout, '')

    def test_installer_os_floor(self):
        installer = self.root / 'install.sh'
        original = (SKILL / 'templates/website/public/install.sh').read_text()
        installer.write_text(original.replace('__MIN_MACOS__', '27.2'))
        self.stub('uname', 'echo arm64')
        self.stub('curl', 'echo reached-download >&2; exit 8')
        self.stub('hdiutil', 'exit 0')
        for version, supported in [('26.9', False), ('27', False), ('27.1.9', False),
                                   ('27.2', True), ('27.2.1', True), ('27.10', True), ('28', True)]:
            with self.subTest(version=version):
                self.stub('sw_vers', f'echo {version}')
                result = self.run_command('sh', installer, ok=False)
                self.assertEqual('reached-download' in result.stderr, supported)
                if not supported:
                    self.assertIn('needs macOS 27.2', result.stderr)

    @unittest.skipUnless(MAC, 'uses macOS template tools')
    def test_scaffold_preserves_binary(self):
        skill = self.root / 'skill'
        shutil.copytree(SKILL / 'templates/app', skill / 'templates/app')
        (skill / 'scripts').mkdir()
        script = skill / 'scripts/scaffold.sh'
        shutil.copy(SKILL / 'scripts/scaffold.sh', script)
        data = b'\x89PNG\x00__EXEC__\xff'
        (skill / 'templates/app/Packaging/icon.png').write_bytes(data)
        self.run_command('bash', script, 'project', 'Tide Log', 'TideLog', 'com.example.tide', '27')
        project = self.root / 'project'
        self.assertEqual((project / 'Packaging/icon.png').read_bytes(), data)
        self.assertTrue((project / 'Sources/TideLog/TideLogApp.swift').is_file())
        self.assertIn('TideLog', (project / 'Package.swift').read_text())

    @unittest.skipUnless(MAC, 'uses macOS code signing and directory exchange')
    def test_install_preserves_existing_app_on_failure(self):
        source = self.root / 'Fixture.app'
        contents = source / 'Contents'
        (contents / 'MacOS').mkdir(parents=True)
        shutil.copy('/usr/bin/true', contents / 'MacOS/Fixture')
        (contents / 'Info.plist').write_bytes(plistlib.dumps(dict(
            CFBundleExecutable='Fixture', CFBundleIdentifier='com.example.fixture', CFBundlePackageType='APPL')))
        self.run_command('codesign', '--force', '-s', '-', source)
        dest = self.root / 'Applications'
        dest.mkdir()
        script = self.root / 'install.sh'
        text = (SKILL / 'templates/app/Scripts/install-app.sh').read_text()
        script.write_text(text.replace('__APP_NAME__', 'Fixture').replace('__EXEC__', 'Fixture'))
        self.run_command('sh', script, source, dest)
        installed = dest / source.name
        marker = installed / 'previous'
        marker.touch()
        self.stub('ditto', 'mkdir -p "$2"; touch "$2/partial"; exit 1')
        self.run_command('sh', script, source, dest, ok=False)
        self.assertTrue(marker.exists())
        (self.bin / 'ditto').unlink()
        (contents / 'MacOS/Fixture').write_bytes(b'invalid binary')
        self.run_command('sh', script, source, dest, ok=False)
        self.assertTrue(marker.exists())
        shutil.copy('/usr/bin/true', contents / 'MacOS/Fixture')
        self.run_command('codesign', '--force', '-s', '-', source)
        self.run_command('sh', script, source, dest)
        self.assertFalse(marker.exists())
        self.run_command('codesign', '--verify', '--deep', '--strict', installed)

    @unittest.skipUnless(MAC, 'uses Swift CryptoKit')
    def test_update_uses_an_independent_key(self):
        # RFC 8032 section 7.1, test 2. The candidate and its signature agree even with a different release pin.
        def b64(value):
            return base64.b64encode(bytes.fromhex(value)).decode()
        key = b64('3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c')
        other_key = b64('d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a')
        sig = b64('92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da'
                  '085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00')
        contents = self.root / 'Fixture.app/Contents'
        contents.mkdir(parents=True)
        (contents / 'Info.plist').write_bytes(plistlib.dumps(dict(SUPublicEDKey=key, CFBundleVersion='1')))
        (self.root / 'archive').write_bytes(b'r')
        (self.root / 'notes').write_text('Release')
        attributes = f'sparkle:edSignature="{sig}" length="1"'
        feed = self.run_command('sh', RELEASE / 'appcast.sh', '1', '1', 'https://example.org/app', attributes, 'notes')
        (self.root / 'appcast.xml').write_text(feed.stdout)
        self.run_command('swiftc', RELEASE / 'verify-update.swift', '-o', 'verify')
        args = ['./verify', 'Fixture.app', 'archive', 'appcast.xml']
        self.run_command(*args, key)
        self.run_command(*args, other_key, ok=False)
        (self.root / 'archive').write_bytes(b's')
        self.run_command(*args, key, ok=False)


if __name__ == '__main__':
    unittest.main()
