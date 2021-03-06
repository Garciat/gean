# type: ignore

import sys
import subprocess


def parse_version(s):
  return tuple(map(int, s.split('.')))


def read_current_version():
  with open('VERSION', 'r') as f:
    return parse_version(f.read())


def update_current_version(ver):
  with open('VERSION', 'w') as f:
    f.write('.'.join(map(str, ver)))


def assert_clean_working_tree():
  diff = subprocess.check_output(['git', 'status', '-s'])
  if diff:
    raise Exception('Working tree is dirty')


def assert_tests_pass():
  subprocess.check_call(['python3', 'setup.py', 'test'])


def _main():
  subprocess.check_call(['git', 'fetch', 'origin', 'master'])

  assert_clean_working_tree()

  assert_tests_pass()

  cur = read_current_version()
  print('Current version:', cur)

  new = parse_version(input('Input new version: '))

  if new <= cur:
    raise Exception('New version is not greater')

  print('Writing version file')
  update_current_version(new)

  subprocess.check_call(['git', 'diff', 'VERSION'])

  if input('Proceed? ').lower() != 'y':
    subprocess.check_call(['git', 'checkout', 'VERSION'])
    exit(1)

  subprocess.check_call(['git', 'commit', '-am', 'Prepare for release'])

  subprocess.check_call(['python3', 'setup.py', 'sdist', 'bdist_wheel'])

  if input('Upload? ').lower() != 'y':
    exit(1)

  subprocess.check_call(['python3', '-m', 'twine', 'upload', '--repository', 'pypi', 'dist/*'])


if __name__ == "__main__":
  _main()
