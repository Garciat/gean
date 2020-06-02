import os.path
import subprocess
import tempfile

from gean import Container, includes


def test_readme_examples() -> None:
  with open('README.md', 'r') as f:
    readme = f.read()

  examples = []

  for chunk in readme.split('```python')[1:]:
    examples.append(chunk.split('```')[0])

  # tried using `exec` but type hint resolution was broken?
  with tempfile.TemporaryDirectory() as tmpdirname:
    for i, example in enumerate(examples):
      filename = 'example{}.py'.format(i + 1)
      filepath = os.path.join(tmpdirname, filename)

      with open(filepath, 'w') as f:
        f.write(example)

      subprocess.check_call(['python3', filepath])
