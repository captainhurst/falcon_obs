import falcon
import simplejson as json
import math
import datetime


class RequireJSON(object):
	def process_request(self, req, resp):
		if not req.client_accepts_json:
			raise falcon.HTTPNotAcceptable(
				'This API only supports responses encoded as JSON.',
				href='http://docs.examples.com/api/json')

		if req.method in ('POST', 'PUT'):
			if 'application/json' not in req.content_type:
				raise falcon.HTTPUnsupportedMediaType(
					'This API only supports requests encoded as JSON.',
					href='http://docs.examples.com/api/json')


class JSONTranslator(object):

	def process_request(self, req, resp):
		if req.content_length in (None, 0):
			return

		body = req.stream.read()
		if not body:
			raise falcon.HTTPBadRequest('Empty request body',
				'A valid JSON document is required.')
		try:
			req.context['doc'] = json.loads(body.decode('utf-8'))

		except (ValueError, UnicodeDecodeError):
			raise falcon.HTTPError(falcon.HTTP_753,
				'Malformed JSON',
				'Could not decode the request body. The '
				'JSON was incorrect or not encoded as '
				'UTF-8.')

api = application = falcon.API(middleware=[
	RequireJSON(),
	JSONTranslator(),
	])

"""
Provide a simple web service application using the falcon framework
in python3 with a web service that accepts 17-digits,
calculates the Luhn check digit, and returns the full 18-digit card 
number to the requestor.
"""

def _roundup(x):
	return int(math.ceil(x / 10.0) * 10)

# Taken from here: http://stackoverflow.com/questions/21079439/implementation-of-luhn-formula -- slightly adapted
def _luhn_checksum(card_number):
    
    def digits_of(n):
        return [int(d) for d in str(n)]
    
    digits = digits_of(card_number)
    odd_digits = digits[::2]
    even_digits = digits[1::2]
    checksum = 0
    checksum += sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d*2))
    return checksum


class LuhnCheck(object):
	"""
	Receives posted object formatted thus:

	{
	  ‘iin’: ‘string of digits’,
	  ‘bin’: ‘string of 2 digits’,
	  ‘sponsor’: ‘string of 2 digits’,
	  ‘account’: ‘string of 7 digits’
	} 

	returns object:

	{
	  ‘cardnumber’: ‘string of 18 digits’,
	  ‘datetime_generated’: ‘datetime in UTC’
	}  
	"""
	def on_post(self, request, response):
		try:
			context = {}
			components = request.context['doc']
			# convert card number parts to cardnumber
			cardnumber = components['iin'] + components['bin'] + components['sponsor'] + components['account']
			# Get Luhnsum
			luhnsum = _luhn_checksum(cardnumber)
			# Round up to the next 10
			next10 = _roundup(luhnsum)
			# Find the last number of the sequence
			last_number = next10 - luhnsum
			context['cardnumber'] = cardnumber + str(last_number)
			context['datetime_generated'] = str(datetime.datetime.now())
			response.body = json.dumps(context)
			response.content_type = 'application/json'
			response.status = falcon.HTTP_200
		except:
			raise falcon.HTTPBadRequest("We're sorry.","Something seems to be wrong.")

# Routes
api.add_route('/luhn-check', LuhnCheck())
