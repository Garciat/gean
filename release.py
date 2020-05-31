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
  subprocess.call(['python3', 'setup.py', 'test'])


def _main():
  assert_clean_working_tree()

  assert_tests_pass()

  cur = read_current_version()
  print('Current version:', cur)

  new = parse_version(input('Input new version: '))

  if new <= cur:
    raise Exception('New version is not greater')

  print('Writing version file')
  update_current_version(new)

  subprocess.call(['git', 'diff', 'VERSION'])

  if input('Proceed? ').lower() != 'y':
    subprocess.call(['git', 'checkout', 'VERSION'])
    exit(1)

  subprocess.call(['git', 'commit', '-am', 'Prepare for release'])

  subprocess.call(['python3', 'setup.py', 'sdist', 'bdist_wheel'])

  subprocess.call(['python3', '-m', 'twine', 'upload', '--repository', 'pypi', 'dist/*'])


if __name__ == "__main__":
  _main()
