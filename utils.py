# encoding: utf-8
import logging
from pathlib import Path
from typing import Union, Any
from urllib.request import urlretrieve
import os

import requests
import yaml
from mutagen.id3 import ID3, APIC
from mutagen.mp3 import MP3

__all__ = ['check_filename', 'mkdir', 'touch_file', 'write_file', 'download_audio', 'add_mp3_cover', 'dump_yaml',
           'load_yaml']

logger = logging.getLogger(__name__)


def check_filename(file_name):
    """
        校验文件名称的方法，在 windows 中文件名不能包含('\','/','*','?','<','>','|') 字符
    Args:
        file_name: 文件名称
    Returns:
        修复后的文件名称
    """
    return file_name.replace('\\', '') \
        .replace('/', '') \
        .replace('*', 'x') \
        .replace('?', '') \
        .replace('<', '《') \
        .replace('>', '》') \
        .replace('|', '_') \
        .replace('\n', '') \
        .replace('\b', '') \
        .replace('\f', '') \
        .replace('\t', '') \
        .replace('\r', '')


def mkdir(path: Union[str, Path]) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)

    return p


def touch_file(path: Union[str, Path]) -> Path:
    p = Path(path)
    p.touch(exist_ok=True)

    return path


def write_file(path: Union[str, Path], content: str, mode: str = 'w') -> Path:
    p = Path(path).resolve()
    with p.open(mode, encoding='utf-8') as f:
        f.write(content)

    return p


def download_audio(audio_url, file_name: Union[str, Path], audio_cover=''):
    if Path(file_name).resolve().exists():
        os.remove(file_name)

    urlretrieve(audio_url, file_name)
    try:
        add_mp3_cover(file_name, audio_cover)
    except Exception as e:
        logger.warning('保存mp3文件封面失败 %s', e)


def add_mp3_cover(audio_name: Union[str, Path], pic_url: str):
    """mp3 音频添加封面"""
    audio = MP3(audio_name, ID3=ID3)

    res = requests.get(pic_url)
    assert res.status_code < 400, '获取文章封面失败 {}'.format(res.status_code)

    audio.tags.add(
        APIC(
            encoding=3,  # 3 is for utf-8
            mime='image/jpeg' if pic_url.endswith('jpg') else 'image/png',
            type=3,  # 3 is for the cover image
            desc=u'Cover',
            data=res.content
        )
    )
    audio.save()


def load_yaml(file_name: Union[Path, str]):
    with open(file_name, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def dump_yaml(data: Any, file_name: Union[Path, str]):
    with open(file_name, 'w', encoding='utf-8') as f:
        return yaml.safe_dump(data, f)
