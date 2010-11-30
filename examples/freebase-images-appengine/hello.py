import cgi
import os

from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

import freebase

class Search(db.Model):
  author = db.UserProperty()
  id = db.StringProperty()
  url = db.StringProperty()
  name = db.StringProperty()
  date = db.DateTimeProperty(auto_now_add=True)

class MainPage(webapp.RequestHandler):
    def get(self):

        searches = []
        searches_avail = False

        user = users.get_current_user()

        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            searches = Search.gql("where author = :author order by date desc limit 5", author=user)
            try:
                searches[0]
                searches_avail = True
            except:
                pass
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login to Google'

        template_values = {
            'user' : user,
            'searches': searches,
            'searches_avail' : searches_avail,
            'url': url,
            'url_linktext': url_linktext,
        }

        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

class Name(webapp.RequestHandler):
  def get(self):
    
    query = { "id" : cgi.escape(self.request.get('id')), "name" : None} 
    r = freebase.mqlread(query)     
    self.response.out.write(r.name)


class Recents(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        final = ""

        if user:
            final = "<strong>Your Recent Searches:</strong> "
            searches = Search.gql("where author = :author order by date desc limit 5", author=user)
            bignum = -1
            for num, search in enumerate(searches):
                final += "<a href='?id=" + search.id + "'>" + search.name + "</a>, "
                bignum = num
            
            final = final[:-2]
            
            if bignum == -1:
                final = ""
        
    
        if not user:
            final = ""

        self.response.out.write(final) 
    
class Info(webapp.RequestHandler):
  def get(self):
    VIEW = "?id="
    BASE = "http://api.freebase.com/api/trans/image_thumb"
    OPTIONS = "?maxheight=300"
    
    id = cgi.escape(self.request.get('id'))

    if id != "":
        info_query = {
            "id" : id,
            "name" : None,    
        }
    
        info = freebase.mqlread(info_query)
        
        user = users.get_current_user()
        search = Search()
        if user:
            search.author = user
        search.id = id
        search.name = info.name
        search.url = VIEW + id
        search.put()
        
    
        query = {
            "id": id,
            "/type/reflect/any_reverse": [{
              "id" : None,
              "/common/topic/image": [{
                "id":       None,
                "optional": True,
                "limit": 5
              }]
            }]
        }
        results = freebase.mqlread(query)
        images = dict()
        for thing in results["/type/reflect/any_reverse"]:
            imgroup = thing['/common/topic/image']
            if len(imgroup) > 0:
                for image in imgroup:
                    images[VIEW + thing["id"]] = BASE + image['id'] + OPTIONS
    
        #template_values = {"images": images}
        #path = os.path.join(os.path.dirname(__file__), 'images.html')
        #self.response.out.write(template.render(path, template_values))
    
        final = ""
        for page, image in images.items():
            final += "<a href='" + page + "'><img src='" + image + "' alt='' /></a>"
        if len(final) == 0:
            final = "Sorry, there are no images to show."
        self.response.out.write(final)
    
    

application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/info', Info),
                                      ('/name', Name),
                                      ('/recents', Recents)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
