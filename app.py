#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
from models import *
from forms import *
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_wtf.csrf import CSRFProtect
import datetime

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

csrf = CSRFProtect()
app = Flask(__name__)

moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)
csrf.init_app(app)

#----------------------------------------------------------------------------#
# models.
#----------------------------------------------------------------------------#
# in models.py


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')

#  Venues
#  ----------------------------------------------------------------


@app.route('/venues')
def venues():

    distinct_city_state_list = Venue.query.distinct(
        Venue.city, Venue.state).all()
    data = []
    for dcsl in distinct_city_state_list:
        data.append({'city': dcsl.city, 'state': dcsl.state, 'venues': []})
        for venue_city_state in Venue.query.filter(Venue.city == dcsl.city, Venue.state == dcsl.state).all():
            data[-1]['venues'].append({'id': venue_city_state.id, 'name': venue_city_state.name,
                                       'num_upcoming_shows': Show.query.filter(Show.venue_id == venue_city_state.id, Show.start_time > datetime.datetime.now()).count()})
    return render_template('pages/venues.html', areas=data)

#  Search Venue
#  ----------------------------------------------------------------


@app.route('/venues/search', methods=['POST'])
def search_venues():

    search_word = request.form.get('search_term', '')
    venues = Venue.query.filter(Venue.name.ilike(
        "%{0}%".format(search_word))).all()
    response = {"count": len(venues), "data": []}
    for venue in venues:
        response['data'].append({'id': venue.id, 'name': venue.name,
                                 'num_upcoming_shows': Show.query.filter(Show.venue_id == venue.id, Show.start_time > datetime.now()).count()})

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

    venue = Venue.query.get(venue_id)
    past_shows = db.session.query(Show).join(Artist).filter(Show.venue_id == venue.id).filter(
        Show.start_time > datetime.datetime.now()
    ).all()
    upcoming_shows = db.session.query(Show).join(Artist).filter(Show.venue_id == venue.id).filter(
        Show.start_time < datetime.datetime.now()
    ).all()
    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": [{
            'artist_id': show.artist_id,
            'artist_name': show.show_artist.name,
            'artist_image_link': show.show_artist.image_link,
            'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        } for show in past_shows],
        "upcoming_shows": [{
            'artist_id': show.artist_id,
            'artist_name': show.show_artist.name,
            'artist_image_link': show.show_artist.image_link,
            'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        } for show in upcoming_shows],
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
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
    venue_form = VenueForm(request.form)
    if venue_form.validate_on_submit():
        try:
            venue = Venue(
                name=request.form['name'],
                genres=request.form.getlist('genres'),
                address=request.form['address'],
                city=request.form['city'],
                state=request.form['state'],
                phone=request.form['phone'],
                facebook_link=request.form['facebook_link'],
                image_link=request.form['image_link'],
                website_link=request.form['website_link'],
                seeking_talent=True if 'seeking_talent' in request.form else False,
                seeking_description=request.form['seeking_description']
            )
            db.session.add(venue)
            db.session.commit()
            flash('Venue ' + request.form['name'] +
                  ' was successfully listed!')
        except:
            flash('An error occurred. Venue ' +
                  request.form['name'] + ' could not be listed.')
            db.session.rollback()
        finally:
            db.session.close()
    else:
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be listed.')
        for error_field in venue_form.errors:
            for error in venue_form[error_field].errors:
                flash(error)
    return render_template('pages/home.html')

#  Delete Venue
#  ----------------------------------------------------------------


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        flash('Venue ' + venue.name + ' was successfully deleted!')
    except:
        db.session.rollback()
        flash('An error occurred. Venue ' +
              venue.name + ' could not be deletd.')
    finally:
        db.session.close()
    return None

#  Update Venue
#  ----------------------------------------------------------------


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)
    edited_venue = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website_link": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
    }
    form = VenueForm(data=edited_venue)
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    venue_form = VenueForm(request.form)
    venue = Venue.query.get(venue_id)
    if venue_form.validate_on_submit():
        try:
            venue.name = request.form['name']
            venue.genres = request.form.getlist('genres')
            venue.address = request.form['address']
            venue.city = request.form['city']
            venue.state = request.form['state']
            venue.phone = request.form['phone']
            venue.facebook_link = request.form['facebook_link']
            venue.image_link = request.form['image_link']
            venue.website_link = request.form['website_link']
            venue.seeking_talent = True if 'seeking_talent' in request.form else False
            venue.seeking_description = request.form['seeking_description']
            db.session.commit()
            flash('Venue ' + request.form['name'] +
                  ' was successfully edited!')
        except:
            flash('An error occurred. Venue ' +
                  request.form['name'] + ' could not be edited.')
            db.session.rollback()
        finally:
            db.session.close()
    else:
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be edited.')
        for error_field in venue_form.errors:
            for error in venue_form[error_field].errors:
                flash(error)

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Artists
#  ----------------------------------------------------------------


@ app.route('/artists')
def artists():

    data = Artist.query.all()
    return render_template('pages/artists.html', artists=data)

#  Search Artist
#  ----------------------------------------------------------------


@ app.route('/artists/search', methods=['POST'])
def search_artists():

    search_word = request.form.get('search_term', '')
    artists = Artist.query.filter(
        Artist.name.ilike("%{0}%".format(search_word))).all()
    response = {"count": len(artists), "data": []}
    for artist in artists:
        response['data'].append({'id': artist.id, 'name': artist.name,
                                 'num_upcoming_shows': Show.query.filter(Show.artist_id == artist.id, Show.start_time > datetime.now()).count()})

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@ app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

    artist = Artist.query.get(artist_id)
    past_shows = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(
        Show.start_time > datetime.datetime.now()
    ).all()
    upcoming_shows = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(
        Show.start_time < datetime.datetime.now()
    ).all()
    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": [{
            'venue_id': show.venue_id,
            'venue_name': show.show_venue.name,
            'venue_image_link': show.show_venue.image_link,
            'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        } for show in past_shows],
        "upcoming_shows": [{
            'venue_id': show.venue_id,
            'venue_name': show.show_venue.name,
            'venue_image_link': show.show_venue.image_link,
            'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        } for show in upcoming_shows],
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_artist.html', artist=data)

#  Create Artist
#  ----------------------------------------------------------------


@ app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@ app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    artist_form = ArtistForm(request.form)
    if artist_form.validate_on_submit():
        try:
            artist = Artist(
                name=request.form['name'],
                genres=request.form.getlist('genres'),
                city=request.form['city'],
                state=request.form['state'],
                phone=request.form['phone'],
                facebook_link=request.form['facebook_link'],
                image_link=request.form['image_link'],
                website_link=request.form['website_link'],
                seeking_venue=True if 'seeking_venue' in request.form else False,
                seeking_description=request.form['seeking_description']
            )

            db.session.add(artist)
            db.session.commit()
            flash('Artist ' + request.form['name'] +
                  ' was successfully listed!')
        except:
            flash('An error occurred. Artist ' +
                  request.form['name'] + ' could not be listed.')
            db.session.rollback()
        finally:
            db.session.close()
    else:
        flash('An error occurred. Artist ' +
              request.form['name'] + ' could not be listed.')
        for error_field in artist_form.errors:
            for error in artist_form[error_field].errors:
                flash(error)
    return render_template('pages/home.html')


#  Delete Artist
#  ----------------------------------------------------------------

@ app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
    try:
        artist = Artist.query.get(artist_id)
        db.session.delete(artist)
        db.session.commit()
        flash('artist ' + artist.name + ' was successfully deleted!')
    except:
        db.session.rollback()
        flash('An error occurred. artist ' +
              artist.name + ' could not be deletd.')
    finally:
        db.session.close()
    return None


#  Update
#  ----------------------------------------------------------------

@ app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    edited_artist = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website_link": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
    }
    form = ArtistForm(data=edited_artist)
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@ app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    artist_form = ArtistForm(request.form)
    artist = Artist.query.get(artist_id)
    if artist_form.validate_on_submit():
        try:
            artist.name = request.form['name']
            artist.genres = request.form.getlist('genres')
            artist.city = request.form['city']
            artist.state = request.form['state']
            artist.phone = request.form['phone']
            artist.facebook_link = request.form['facebook_link']
            artist.image_link = request.form['image_link']
            artist.website_link = request.form['website_link']
            artist.seeking_venue = True if 'seeking_venue' in request.form else False
            artist.seeking_description = request.form['seeking_description']
            db.session.commit()
            flash('Artist ' + request.form['name'] +
                  ' was successfully edited!')
        except:
            flash('An error occurred. Artist ' +
                  request.form['name'] + ' could not be edited.')
            db.session.rollback()
        finally:
            db.session.close()
    else:
        flash('An error occurred. Artist ' +
              request.form['name'] + ' could not be edited.')
        for error_field in artist_form.errors:
            for error in artist_form[error_field].errors:
                flash(error)
    return redirect(url_for('show_artist', artist_id=artist_id))

#  Shows
#  ----------------------------------------------------------------


@ app.route('/shows')
def shows():

    shows = db.session.query(Show).join(Artist).join(Venue).all()
    data = [{
            "venue_id": show.venue_id,
            "venue_name": show.show_venue.name,
            "artist_id": show.artist_id,
            "artist_name": show.show_artist.name,
            "artist_image_link": show.show_artist.image_link,
            "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
            }
            for show in shows]

    return render_template('pages/shows.html', shows=data)


@ app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@ app.route('/shows/create', methods=['POST'])
def create_show_submission():
    show_form = ShowForm(request.form)
    try:
        show = Show(
            venue_id=show_form.venue_id.data,
            artist_id=show_form.artist_id.data,
            start_time=show_form.start_time.data
        )
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
    except:
        db.session.rollback()
        flash('An error occurred. Show could not be listed.')
    finally:
        db.session.close()
        return render_template('pages/home.html')


@ app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@ app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
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
