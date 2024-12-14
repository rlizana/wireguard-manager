import os
import shutil
import unittest

from wgm.__main__ import create_app
from cleo.testers.command_tester import CommandTester


class TestWGM(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.app = create_app()
        self.config_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), 'etc_wireguard')

    def reset_test_folder(self):
        if os.path.exists(self.config_path):
            shutil.rmtree(self.config_path)
        sample_path = os.path.join(os.path.dirname(__file__), 'sample')
        shutil.copytree(sample_path, self.config_path)

    def execute(self, txt):
        args = txt.split(' ')
        name = args.pop(0)
        cmd = CommandTester(self.app.find(name))
        args.append(f'--config-path={self.config_path}')
        result_code = cmd.execute(' '.join(args))
        return result_code, cmd._io.fetch_output()

    def test_path_not_exists(self):
        self.reset_test_folder()
        shutil.rmtree(self.config_path)
        result_code, output = self.execute('list')
        self.assertEqual(result_code, 100)
        self.assertIn('not exists!', output)

    def test_list(self):
        self.reset_test_folder()
        result_code, output = self.execute('list')
        self.assertEqual(result_code, 0)
        self.assertIn('Not users', output)

    def test_create(self):
        self.reset_test_folder()
        result_code, output = self.execute('create username')
        self.assertEqual(result_code, 0)
        self.assertIn('User "username" created.', output)
        user_path = os.path.join(self.config_path, 'clients', 'username')
        self.assertTrue(os.path.exists(user_path))
        result_code, output = self.execute('create username')
        self.assertEqual(result_code, 1)
        self.assertIn('User "username" already exists.', output)

    def test_delete(self):
        self.reset_test_folder()
        result_code, output = self.execute('delete username')
        self.assertEqual(result_code, 1)
        self.assertIn('User "username" not exists.', output)
        self.execute('create username')
        result_code, output = self.execute('delete username')
        self.assertEqual(result_code, 0)
        self.assertIn('User "username" deleted.', output)

    def test_create_list_delete(self):
        self.reset_test_folder()
        result_code, output = self.execute('create username')
        self.assertEqual(result_code, 0)
        result_code, output = self.execute('list')
        self.assertEqual(result_code, 0)
        self.assertIn('username', output)
        result_code, output = self.execute('delete username')
        self.assertEqual(result_code, 0)
        result_code, output = self.execute('list')
        self.assertEqual(result_code, 0)
        self.assertIn('Not users.', output)

    def test_create_user_wg0(self):
        self.reset_test_folder()
        self.execute('create user-1')
        conf_file = os.path.join(
            self.config_path, 'clients', 'user-1', 'user-1.conf')
        self.assertTrue(os.path.exists(conf_file))
        with open(conf_file, 'r') as file:
            conf = file.read()
        self.assertIn('Address = ', conf)
