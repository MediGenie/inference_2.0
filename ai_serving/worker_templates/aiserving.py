from pathlib import Path

__all__ = ('Status', 'update_progress',)

venv_dir = Path(__file__).parent.parent


class Status:
    LOADING = 'loading'
    PREPROCESSING = 'preprocessing'
    INFERENCING = 'inferencing'
    POSTPROCESSING = 'postprocessing'


def update_progress(status: Status, progress: int, total: int):
    progress_path = venv_dir / "progress.txt"
    with progress_path.open('w') as f:
        f.write(f'{status}:{progress}:{total}')
