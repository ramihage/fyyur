from flask_sqlalchemy import SQLAlchemy
from enums import Genre
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
db = SQLAlchemy()


class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(), nullable=False)
    genres = db.Column(db.String(), nullable=False)

    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)

    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    seeking_talent = db.Column(db.Boolean, nullable=False)
    seeking_description = db.Column(db.String())

    website = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    shows = db.relationship(
        'Show', backref='venue', cascade='all, delete-orphan'
        )

    __table_args__ = (db.UniqueConstraint('name', 'city', 'state', 'address'),)


class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(), nullable=False)
    genres = db.Column(db.String(), nullable=False)

    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    
    phone = db.Column(db.String(120), nullable=False)
    seeking_venue = db.Column(db.Boolean, nullable=False)
    seeking_description = db.Column(db.String())

    website = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    shows = db.relationship(
        'Show', backref='artist', cascade='all, delete-orphan'
        )
    availabilities = db.relationship(
        'Availability', backref='artist', cascade='all, delete-orphan'
    )

    __table_args__ = (db.UniqueConstraint('name', 'phone'),)


class  Show(db.Model):
  __tablename__ = 'shows'

  artist_id = db.Column(db.Integer, db.ForeignKey('artists.id', ondelete='CASCADE'), primary_key=True, nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('venues.id', ondelete='CASCADE'), primary_key=True, nullable=False)
  show_date = db.Column(db.Date, primary_key=True, nullable=False)
  show_time = db.Column(db.Time, nullable=False)


class Availability(db.Model):
    __tablename__ = "availabilities"

    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    date = db.Column(db.Date, primary_key=True, nullable=False)
    time = db.Column(db.Time, nullable=False)
