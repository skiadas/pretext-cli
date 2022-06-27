import subprocess, os, shutil, time, signal, platform, random
from tempfile import TemporaryDirectory
from pathlib import Path
from contextlib import contextmanager
import requests
import pretext

EXAMPLES_DIR = Path(__file__).parent/'examples'

def pretext_new_cd(dir="foobar") -> None:
    subprocess.run(["pretext","new","-d",dir])
    os.chdir(Path(dir))

@contextmanager
def pretext_view(*args):
    process = subprocess.Popen(['pretext','view']+list(args))
    time.sleep(1)
    try:
        yield process
    finally:
        process.send_signal(signal.SIGINT)
        time.sleep(1)
        assert process.poll()==0

def cmd_works(*args) -> bool:
    return subprocess.run(args).returncode == 0

def test_entry_points(script_runner):
    ret = script_runner.run('pretext', '-h')
    assert ret.success
    assert subprocess.run(['python', '-m', 'pretext', '-h']).returncode == 0

def test_version(script_runner):
    ret = script_runner.run('pretext', '--version')
    assert ret.stdout.strip() == pretext.VERSION

def test_new(tmp_path:Path,script_runner):
    assert script_runner.run('pretext', 'new', cwd=tmp_path).success
    assert (tmp_path/'new-pretext-project'/'project.ptx').exists()

def test_build(tmp_path:Path,script_runner):
    assert script_runner.run('pretext', 'new', '-d', '.', cwd=tmp_path).success
    assert script_runner.run('pretext', 'build', 'web', cwd=tmp_path).success
    assert (tmp_path/'output'/'web').exists()
    assert script_runner.run('pretext', 'build', 'subset', cwd=tmp_path).success
    assert (tmp_path/'output'/'subset').exists()
    assert script_runner.run('pretext', 'build', 'print-latex', cwd=tmp_path).success
    assert (tmp_path/'output'/'print-latex').exists()
    assert script_runner.run('pretext', 'build', '-g', cwd=tmp_path).success
    assert (tmp_path/'generated-assets').exists()
    os.removedirs(tmp_path/'generated-assets')
    assert script_runner.run('pretext', 'build', '-g', 'webwork', cwd=tmp_path).success
    assert (tmp_path/'generated-assets').exists()

def test_init(tmp_path:Path,script_runner):
    assert script_runner.run('pretext', 'init', cwd=tmp_path).success
    assert (tmp_path/'project.ptx').exists()
    assert (tmp_path/'requirements.txt').exists()
    assert (tmp_path/'.gitignore').exists()
    assert (tmp_path/'publication'/'publication.ptx').exists()
    assert len([*tmp_path.glob('project-*.ptx')]) == 0 # need to refresh
    assert script_runner.run('pretext', 'init', '-r', cwd=tmp_path).success
    assert len([*tmp_path.glob('project-*.ptx')]) > 0
    assert len([*tmp_path.glob('requirements-*.txt')]) > 0
    assert len([*tmp_path.glob('.gitignore-*')]) > 0
    assert len([*tmp_path.glob('publication/publication-*.ptx')]) > 0

def test_generate(tmp_path:Path):
    os.chdir(tmp_path)
    subprocess.run(['pretext', 'init'])
    Path('source').mkdir()
    shutil.copyfile(EXAMPLES_DIR/'asymptote.ptx',Path('source')/'main.ptx')
    assert cmd_works('pretext','generate','asymptote')
    assert (Path('generated-assets')/'asymptote'/'test.html').exists()
    os.remove(Path('generated-assets')/'asymptote'/'test.html')
    assert cmd_works('pretext','generate','-x','test')
    assert (Path('generated-assets')/'asymptote'/'test.html').exists()
    os.remove(Path('generated-assets')/'asymptote'/'test.html')
    assert cmd_works('pretext','generate','asymptote', '-t', 'web')
    assert (Path('generated-assets')/'asymptote'/'test.html').exists()

def test_view(tmp_path:Path):
    os.chdir(tmp_path)
    port = random.randint(10_000, 65_636)
    with pretext_view('-d','.','-p',f'{port}'):
        assert requests.get(f'http://localhost:{port}/').status_code == 200
    port = random.randint(10_000, 65_636)
    pretext_new_cd("1")
    subprocess.run(['pretext','build'])
    with pretext_view('-p',f'{port}'):
        assert requests.get(f'http://localhost:{port}/').status_code == 200
    port = random.randint(10_000, 65_636)
    os.chdir(tmp_path)
    pretext_new_cd("2")
    with pretext_view('-p',f'{port}','-b','-g'):
        assert requests.get(f'http://localhost:{port}/').status_code == 200

def test_custom_xsl(tmp_path:Path):
    shutil.copytree(EXAMPLES_DIR/'projects'/'custom-xsl',tmp_path/'custom')
    os.chdir(tmp_path/'custom')
    assert cmd_works('pretext','build')
    assert (Path('output')/'test').exists()
