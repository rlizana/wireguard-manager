from dataclasses import dataclass, field


@dataclass
class Entry:
    key: str = ''
    value: str = ''
    raw: str = ''

    @property
    def is_raw(self):
        return not self.key


@dataclass
class Section:
    name: str
    entries: list = field(default_factory=list)

    def values(self, key):
        return [entry.value for entry in self.entries if entry.key == key]

    def get(self, key, default=''):
        values = self.values(key)
        return values[0] if values else default

    def set(self, key, value):
        for entry in self.entries:
            if entry.key == key:
                entry.value = value
                return
        self.entries.append(Entry(key=key, value=value))

    def remove(self, key):
        self.entries = [entry for entry in self.entries if entry.key != key]


@dataclass
class Conf:
    items: list = field(default_factory=list)

    @classmethod
    def parse(cls, text):
        conf = cls()
        current = None
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith('[') and stripped.endswith(']'):
                current = Section(name=stripped[1:-1])
                conf.items.append(current)
            elif current is None:
                conf.items.append(Entry(raw=line))
            elif not stripped or stripped.startswith('#'):
                current.entries.append(Entry(raw=line))
            elif '=' in stripped:
                key, value = stripped.split('=', 1)
                current.entries.append(
                    Entry(key=key.strip(), value=value.strip())
                )
            else:
                current.entries.append(Entry(raw=line))
        return conf

    @classmethod
    def load(cls, path):
        return cls.parse(path.read_text())

    def sections(self, name):
        return [
            item
            for item in self.items
            if isinstance(item, Section) and item.name == name
        ]

    def section(self, name):
        found = self.sections(name)
        return found[0] if found else None

    def add_section(self, name):
        section = Section(name=name)
        self.items.append(section)
        return section

    def remove(self, section):
        self.items = [item for item in self.items if item is not section]

    def render(self):
        lines = []
        for item in self.items:
            if not isinstance(item, Section):
                lines.append(item.raw)
                continue
            lines.append(f'[{item.name}]')
            for entry in item.entries:
                if entry.is_raw:
                    lines.append(entry.raw)
                else:
                    lines.append(f'{entry.key} = {entry.value}')
            if lines[-1].strip():
                lines.append('')
        while lines and not lines[-1].strip():
            lines.pop()
        return '\n'.join(lines) + '\n'
