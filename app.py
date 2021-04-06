#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import sys
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect,\
                  url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
# db imported from models.py
db.init_app(app)

migrate = Migrate(app, db)
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  # 10 most recently added venues
  venues = Venue.query.order_by(db.desc(Venue.id)).limit(10).all()
  # 10 most recently added artists
  artists = Artist.query.order_by(db.desc(Artist.id)).limit(10).all()
  
  return render_template('pages/home.html', venues=venues, artists=artists)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data = list()
  city_states = db.session.query(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
  for (city, state) in city_states:
    venues = Venue.query.filter_by(city=city, state=state).all()
    venue_data = list()
    for venue in venues:
      # Get upcoming shows
      now = datetime.now()
      today = now.date()
      upcoming_shows = Show.query.filter(
      Show.venue_id == venue.id, Show.show_date >= today
      ).count()

      venue_data.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": upcoming_shows
      })

    data.append({
          "city": city,
          "state": state,
          "venues": venue_data
        })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form['search_term']
  results = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
  data = list()
  for venue in results:
    today = datetime.today().date()
    upcoming_shows_count = Show.query.filter(
      Show.show_date >= today, Show.venue_id == venue.id).count()
    
    data.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": upcoming_shows_count
    })

  response={
    "count": len(results),
    "data": data
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/searchbycitystate', methods=['POST'])
def search_venues_by_city_state():
  search_term = request.form['search_term']
  try:
    city, state = search_term.split(',')[0].strip(), search_term.split(',')[1].strip()
    results = Venue.query.filter(
      Venue.city == city, Venue.state == state
    ).all()

    data = list()
    for venue in results:
      today = datetime.today().date()
      upcoming_shows_count = Show.query.filter(
        Show.show_date >= today, Show.venue_id == venue.id).count()
      
      data.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": upcoming_shows_count
      })
  except IndexError:
    results = list()
    data = list()

  response={
    "count": len(results),
    "data": data
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  now = datetime.now()
  today = now.date()
  venue = Venue.query.get(venue_id)
  genres = venue.genres.split(";")
  # Get past shows
  results = db.session.query(
    Show, Artist
    ).join(Venue.shows).join(Show.artist).filter(
      Show.venue_id == venue_id, Show.show_date < today
    )

  past_shows = list()
  past_count = results.count()
  # Return query results
  results = results.all()
  for (show, artist) in results:
    showdatetime = datetime.combine(show.show_date, show.show_time)
    past_shows.append({
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": showdatetime.isoformat()
    })

  # Get upcoming shows
  results = db.session.query(
    Show, Artist
    ).join(Venue.shows).join(Show.artist).filter(
      Show.venue_id == venue_id, Show.show_date >= today
    )

  upcoming_shows = list()
  upcoming_count = results.count()
  # Return query results
  results = results.all()
  for (show, artist) in results:
    showdatetime = datetime.combine(show.show_date, show.show_time)
    upcoming_shows.append({
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": showdatetime.isoformat()
    })
  
  # Populate data to be sent to template
  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  genres = ";".join(request.form.getlist('genres'))
  try:
    venue = Venue(
      name=request.form['name'],
      genres=genres,
      city=request.form['city'],
      state=request.form['state'],
      address=request.form['address'],
      phone=request.form['phone'],
      facebook_link=request.form['facebook_link'],
      image_link=request.form['image_link'],
      website=request.form['website_link'],
      seeking_talent=True if 'seeking_talent' in request.form else False,
      seeking_description=request.form['seeking_description']
    )

    db.session.add(venue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash(
      'An error occurred. Venue ' + request.form['name'] + ' could not be listed.',
      'error'
      )
  finally:
    db.session.close()

  return redirect(url_for('index'))

@app.route('/venues/<venue_id>/delete', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash('Venue deleted successfully.')
  except:
    db.session.rollback()
    flash(
      'An error occured. Could not delete Venue',
      'error'
      )
  finally:
    db.session.close()

  return jsonify({'success': True})

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  all_artists = Artist.query.all()
  data = list()
  for artist in all_artists:
    data.append({
      "id": artist.id,
      "name": artist.name
    })
  
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form['search_term']
  results = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
  data = list()
  for artist in results:
    today = datetime.today().date()
    num_upcoming_shows = Show.query.filter(
      Show.show_date >= today, Show.artist_id == artist.id
    ).count()

    data.append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": num_upcoming_shows,
    })

  response={
    "count": len(results),
    "data": data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/searchbycitystate', methods=['POST'])
def search_artists_by_city_state():
  search_term = request.form['search_term']
  try:
    city, state = search_term.split(',')[0].strip(), search_term.split(',')[1].strip()
    results = Artist.query.filter(
      Artist.city == city, Artist.state == state
    ).all()

    data = list()
    for artist in results:
      today = datetime.today().date()
      upcoming_shows_count = Show.query.filter(
        Show.show_date >= today, Show.artist_id == artist.id).count()
      
      data.append({
        "id": artist.id,
        "name": artist.name,
        "num_upcoming_shows": upcoming_shows_count
      })
  except IndexError:
    results = list()
    data = list()

  response={
    "count": len(results),
    "data": data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  now = datetime.now()
  today = now.date()
  artist = Artist.query.get(artist_id)
  genres = artist.genres.split(";")
  # Query for next 5 available dates
  available = db.session.query(Availability).filter(
    Availability.artist == artist, Availability.date >= today
  ).order_by(Availability.date).limit(5).all()
  # Convert availabilities to datetime.isoformat()
  availabilities = [
    datetime.combine(a.date, a.time).isoformat() for a in available
    ]
  
  # Get past shows
  results = db.session.query(
    Venue, Show
  ).join(Show.venue).join(Show.artist).filter(
    Show.artist_id == artist.id, Show.show_date < today
  )

  past_shows = list()
  past_count = results.count()
  for (venue, show) in results.all():
    showdatetime = datetime.combine(show.show_date, show.show_time)
    past_shows.append({
      "venue_id": venue.id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": showdatetime.isoformat()
    })

  # Get upcoming shows
  results = db.session.query(
    Venue, Show
  ).join(Show.venue).join(Show.artist).filter(
    Show.artist_id == artist.id, Show.show_date >= today
  )

  upcoming_shows = list()
  upcoming_count = results.count()
  for (venue, show) in results.all():
    showdatetime = datetime.combine(show.show_date, show.show_time)
    upcoming_shows.append({
      "venue_id": venue.id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": showdatetime.isoformat()
    })
  
  # Populate data to be sent to template
  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
    "availabilities": availabilities
  }
  
  return render_template('pages/show_artist.html', artist=data)

#  Artist Availability
#  ----------------------------------------------------------------
@app.route('/artists/<artist_id>/add_availability', methods=['GET'])
def add_availability(artist_id):
  artist = Artist.query.get(artist_id)
  form = AvailabilityForm()

  return render_template('forms/new_availability.html', form=form, artist=artist)

@app.route('/artists/<artist_id>/add_availability', methods=['POST'])
def add_availability_submission(artist_id):
  artist = Artist.query.get(artist_id)
  try:
    # Parse availability into a datetime object
    available_datetime = dateutil.parser.parse(request.form['start_time'])

    availability = Availability(
      date=available_datetime.date(), time=available_datetime.time()
    )
    availability.artist = artist
    db.session.add(availability)
    db.session.commit()
  except:
    db.session.rollback()
    flash('An error occured, listing could not be submitted.')
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))
#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  genres = [g.name for g in artist.genres]

  form = ArtistForm()
  form.name.data = artist.name
  form.genres.data = genres
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.website_link.data = artist.website
  form.facebook_link.data = artist.facebook_link
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description
  form.image_link.data = artist.image_link
  
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:
    artist = Artist.query.get(artist_id)
    artist_genres = list()
    for genrename in request.form.getlist('genres'):
      artist_genres.append(Genre.query.filter_by(name=genrename).first())
    
    artist.genres = artist_genres
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.facebook_link = request.form['facebook_link']
    artist.image_link = request.form['image_link']
    artist.website = request.form['website_link']
    artist.seeking_venue = True if 'seeking_venue' in request.form else False
    artist.seeking_description = request.form['seeking_description']

    db.session.commit()
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash(
      'An error occurred. Artist ' + artist.name + ' could not be Edited.',
      'error'
      )
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  genres = [g.name for g in venue.genres]

  form = VenueForm()
  form.name.data = venue.name
  form.genres.data = genres
  form.address.data = venue.address
  form.city.data = venue.city
  form.state.data = venue.state
  form.phone.data = venue.phone
  form.website_link.data = venue.website
  form.facebook_link.data = venue.facebook_link
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description
  form.image_link.data = venue.image_link
  
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
    venue = Venue.query.get(venue_id)
    venue_genres = list()
    for genrename in request.form.getlist('genres'):
      venue_genres.append(Genre.query.filter_by(name=genrename).first())
    
    venue.genres = venue_genres
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.facebook_link = request.form['facebook_link']
    venue.image_link = request.form['image_link']
    venue.website = request.form['website_link']
    venue.seeking_talent = True if 'seeking_talent' in request.form else False
    venue.seeking_description = request.form['seeking_description']

    db.session.commit()
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash(
      'An error occurred. Venue ' + venue.name + ' could not be Edited.',
      'error'
      )
  finally:
    db.session.close()
  
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  genres = ";".join(request.form.getlist('genres'))
  try:
    artist = Artist(
      name=request.form['name'],
      genres=genres,
      city=request.form['city'],
      state=request.form['state'],
      phone=request.form['phone'],
      facebook_link=request.form['facebook_link'],
      image_link=request.form['image_link'],
      website=request.form['website_link'],
      seeking_venue=True if 'seeking_talent' in request.form else False,
      seeking_description=request.form['seeking_description']
    )

    db.session.add(artist)
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash(
      'An error occurred. Artist ' + request.form['name'] + ' could not be listed.',
      'error'
      )
  finally:
    db.session.close()

  return redirect(url_for('index'))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # # Get upcoming shows
  now = datetime.now()
  today = now.date()
  results = Show.query.filter(Show.show_date >= today).all()
  data = list()
  for show in results:
    showdatetime = datetime.combine(show.show_date, show.show_time)
    data.append({
      "venue_id": show.venue.id,
      "venue_name": show.venue.name,
      "artist_id": show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": showdatetime.isoformat()
    })
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  message = ''
  try:
    artist = Artist.query.get(request.form['artist_id'])
    venue = Venue.query.get(request.form['venue_id'])
    # If artist doesn't exist in the database
    if not artist:
      error_source = 'Artist'
      source_id = request.form['artist_id']
      message = f"{error_source} with ID {source_id} does not exist."
      raise Exception
    # If venue doesn't exist in the database
    elif not venue:
      error_source = 'Venue'
      source_id = request.form['venue_id']
      message = f"{error_source} with ID {source_id} does not exist."
      raise Exception
    
    show_datetime = dateutil.parser.parse(request.form['start_time'])
    
    # Check if the artist is available at the given date and time
    results = db.session.query(Availability.date, Availability.time).filter(
      Availability.artist == artist, Availability.date == show_datetime.date(),
      Availability.time <= show_datetime.time()
    ).first()
    # If no results are found -> the artist is not available
    if not results:
      message = f"{artist.name} is not available on {request.form['start_time']}"
      raise Exception

    # Check if a show at this venue is already schedueled at the given date
    exist_show = Show.query.filter_by(venue_id=venue.id, show_date=show_datetime.date()).first()
    # If a show is already scheduled at the given time raise an exception
    if exist_show is not None:
      message = f"{venue.name} has already a scheduled show on the {show_datetime.date()}"
      raise Exception

    show = Show(show_date=show_datetime.date(), show_time=show_datetime.time())
    show.artist = artist
    show.venue = venue

    db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash(
      f'An error occurred. Show could not be listed. {message}',
      'error'
      )
  finally:
    db.session.close()
  
  # return render_template('pages/home.html')
  return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
