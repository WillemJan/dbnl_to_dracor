from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Role:
    id: str
    sex: Optional[int] = None
    type: Optional[str] = None
    statut: Optional[str] = None
    age: Optional[str] = None
    stat_amour: Optional[str] = None

@dataclass
class CastItem:
    role: Role
    actor: str

@dataclass
class Set:
    location: str
    country: str
    periode: str
    gps: str

@dataclass
class Note:
    text: str

@dataclass
class Scene:
    head: str
    stage: Optional[str] = None
    speakers: List[dict] = None
    lines: List[dict] = None

@dataclass
class Act:
    type: str
    n: str
    head: str
    scenes: List[Scene]

@dataclass
class Performance:
    premiere_date: str
    location: str
    note: Optional[Note] = None

@dataclass
class Front:
    docTitle: List[str]
    docDate: str
    docAuthor: str
    docImprint: dict
    performance: Performance
    castList: List[CastItem]
    set: Set
    note: Note

@dataclass
class Body:
    acts: List[Act]

@dataclass
class Text:
    front: Front
    body: Body

@dataclass
class Play:
    title: str
    author: str
    year: str
    place_of_publication: str
    publisher: str
    library: str
    category: str
    country: str
    edition: str
    translator: str
    link: str
    shelfmark: str
    full_text: str
    actors: List[dict]
    cast: List[CastItem]
    set_info: Set
    note: Note
    text: Text

author = Author(first_name="D.V.", last_name="Coornhert", prefix="")
translator = Translator(first_name="", last_name="")
edition = Edition(edition_number="1", edition_type="ste druk")
actors = [Actor(actor_name="Actor1", role="Role1"), Actor(actor_name="Actor2", role="Role2")]

play_data = {
    'title': 'Comedie van Israel',
    'author': author,
    'year': '1590',
    'place_of_publication': 'Gouda',
    'publisher': '[Jasper Tournay]',
    'library': 'Universiteitsbibliotheek Amsterdam',
    'category': 'werk',
    'country': 'nl',
    'edition': edition,
    'translator': translator,
    'link': 'https://www.dbnl.org/tekst/coor001come04_01',
    'shelfmark': 'OTM: OK 61-782 (2), scan van Google Books',
    'full_text': 'Insert full text here with placeholders for actors...',
    'actors': actors
}

play_instance = Play(**play_data)
print(play_instance)
