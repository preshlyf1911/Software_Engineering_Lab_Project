import datetime
from django.shortcuts import render, redirect
from django.http.response import Http404,JsonResponse
from django.http import HttpResponse
from .forms import CustomerSignupForm
from .models import Customer,Movie, Show, Booking,Reviews
from .displayErrors import returnError
from django.contrib import messages
from django.views.generic import ListView
from django.db.models import Q
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta


# Create your views here.

def index(request):
   movies = Movie.objects.raw('SELECT * FROM movie_movie where is_screening=%s order by random() limit 4', [1])
   #request.session['username'] = None
   return render(request,'homepg_html/home_page.html', {'movie': movies})

def search_content(request):
    
    search_resume = request.GET.get('search')

    if search_resume:
         resume = Movie.objects.filter(Q(name__icontains=search_resume) | Q(gender__icontains=search_resume))
    else:
        search_ = request.GET.get('search')
        resume = Movie.objects.all().order_by("name")
    return render(request, 'homepg_html/home_page2.html', {'resume': resume})

def autocomplete(request):
    if 'term' in request.GET:
        resume=Movie.objects.filter(name__istartswith=request.GET.get('term'))
        names=[]
        for re in resume:
            names.append(re.name)
        return JsonResponse(names,safe=False)
    return render(request, 'homepg_html/home_page2.html')

        

def customerSignup(request):
    if request.method == 'POST':
        customerForm = CustomerSignupForm(request.POST)
        if len(customerForm.errors) == 1:
            if customerForm.errors['username'] == ['Customer with this Username already exists.'] :
                message = 'The username is already used. Please use anther username.'
                error = 0
                messages.error(request, message)
                return render(request,'customer_html/Signup.html', {'error': error} )

        if customerForm.is_valid():   
            username = customerForm.data['username']
            email = customerForm.data['email']
            password = customerForm.data['password']
            
            customer = Customer(username=username, email=email, password=password)
            customer.save()
        
            return returnError(request, 
                'Your account is succefully created. Please login with your credentials.', 
                'customer_html/login.html', 1)

    return render(request,'customer_html/Signup.html')

def customerLogin(request):
    try:
        if request.session['username'] != None:
            message = 'Please confirm.'
            error = 1
            messages.success(request, message)
            return redirect(customerHome)   
    except Exception as e:
        pass

    if request.method == 'POST':
        username = request.POST['username'] 
        password = request.POST['password'] 
        
        try:
            customer = Customer.objects.get(username=username)
            
            originalPassword = customer.password
            
            if not originalPassword == None:
            
                if originalPassword == password:
                    
                        request.session['username'] = username
                        customer.is_active = True
                        customer.save()
                        return redirect(customerHome)
                else:
                    return returnError(request, 'Incorrect Username or Password', 'customer_html/login.html', 0)
        except Customer.DoesNotExist as e:
                return returnError(request, 'Incorrect Username or Password', 'customer_html/login.html', 0)

    return render(request,'customer_html/login.html')

def customerHome(request):
    try:
        customer = Customer.objects.get(username=request.session['username'] )
        if request.session['username'] != None:
            movies = Movie.objects.raw('SELECT * FROM movie_movie where is_screening=%s order by random() limit 4',[1])
            message = 'You are logged in as \'' + customer.username + '\''
            error = 1
            messages.success(request, message)
            return render(request,'homepg_html/customer_home.html', {'movie': movies, 'error': error, 'username':'  ' + customer.username})

    except Exception as e:
        return redirect(index)
    except customer.DoesNotExist as e:
        return redirect(index)
    
 
def customerLogout(request):
    if request.session['username'] != None:
        
        customer = Customer.objects.get(username=request.session['username'] )
        customer.is_active = False
        customer.save()
        request.session['username'] = None
        
    return redirect(index)


def bookings(request, movie_id):
    #try:
    if request.session['username'] != None:
        try:
            movie = Movie.objects.get(pk= movie_id)
            
            shows = Show.objects.filter(show_movie=movie)
            
            request.session['movie'] = movie.pk
            
            args = {'shows':shows, 'movie':movie}
            
            return render(request, 'bookings/bookings.html', args )
            
        except Exception as e:
            message = 'Some error occurred. Please try again later.' 
            error = 1
            messages.success(request, message) 
            return redirect(customerHome)
    else:
        return redirect(customerLogin) 
    '''  
    except Exception as e:
        return redirect(customerLogin)
    '''

def bookingMovie(request):
    try:
        if request.session['username'] != None:
            
            if request.method == 'POST':                
                customer = Customer.objects.get(username=request.session['username'])
                
                movie_id = request.session['movie']

                movie = Movie.objects.get(pk=movie_id)
                  
                formShow = request.POST['shows']
                
                show = Show.objects.filter(show_movie=movie)
                
                for sh in show:                   
                    if formShow in sh.__str__():
                        showMovie = sh
                
                num_of_tickets = request.POST['num_of_tickets']
                
                show_seats = int(showMovie.show_seats)
                show_booked_seats = int(showMovie.show_booked_seats) + int(num_of_tickets)

                if show_booked_seats > show_seats :
                    message = 'Tickets sold out for Show: ' + str(showMovie) + '.' 
                    error = 0
                    messages.error(request, message)
                    #movies = Movie.objects.raw('SELECT * FROM movie_movie where is_screening=%s order by random() limit 4',[1])
                    #return render(request,'homepg_html/customer_home.html', {'movie': movies, 'error': error, 'username':'  ' + customer.username})
                    return redirect(customerHome)
                else:
                    showMovie.show_booked_seats += int(num_of_tickets)
                    showMovie.save()
            
                try:
                    customerBookings = Booking.objects.get(user=customer, show=showMovie)
                    if customerBookings != None:
                        message = 'Tickets already booked for Show: ' + str(showMovie) + ' || Tickets: ' + str(customerBookings.number_of_tickets) + ' || by you.' 
                        error = 1
                        messages.success(request, message) 

                        return redirect(customerHome)
                
                except Booking.DoesNotExist as e:
                    book = Booking(user=customer, show=showMovie, number_of_tickets=num_of_tickets)
                    book.save()
                    message = 'Tickets successfully booked for Show: ' + str(showMovie) + '.' 
                    error = 1
               
                    messages.success(request, message)
                    return redirect(customerHome)
    except Exception as e:
        return redirect(index)


def comment (request, movie_id):
    if request.session['username'] != None:
        try:
            movie = Movie.objects.get(pk= movie_id)
            #print(movie)
            request.session['movie'] = movie.pk
            args = {'movie':movie}
            #print(args)
            # return render(request, 'comments/comment.html', args )
            
        except Exception as e:
            message = 'Some error occurred. Please try again later.' 
            error = 1
            messages.success(request, message) 
            return redirect(customerHome)
    else:
        
        return redirect(customerLogin) 
    return render(request, 'comments/comment.html', args )

def movieComments(request):      
    try:
        if request.session['username'] != None:
            
            if request.method == 'POST':                
                customer = Customer.objects.get(username=request.session['username'])
                
                movie_id = request.session['movie']

                movie = Movie.objects.get(pk=movie_id)
                
                formComment = request.POST['comment']

                #print(formComment)
                comment = Reviews(disp_movie=movie,feedback_data=formComment,users=customer)
                comment.save()
                message = 'Comment Added'
                error = 1
               
                messages.success(request, message)
                return redirect(customerHome)
    except Exception as e:
        return redirect(index)
    
def pie_chart(request):
    
    labels = ['English','Hindi','Tamil']
    data = []
    queryset = Movie.objects.order_by('movie_name')[:50]
    for city in queryset:
        data.append(city.movie_language)
    
    num_eng=data.count("English")
    num_hin=data.count("Hindi")
    num_tam=data.count("Tamil")
    d=[]
    d.append(num_eng)
    d.append(num_hin)
    d.append(num_tam)
    booking={
        'today':'todays_booking',
        'week' :'week_booking',
        'month' :'month_booking'
        
    }
    return render(request, 'homepg_html/chart.html', {
        'labels': labels,
        'data': d,
        'booking':booking,
        
    })



    
def population_chart(request):
    labels = []
    data = []

    queryset = Customer.objects.values('username').annotate(population=Sum('is_active')).order_by('username')
    for entry in queryset:
        labels.append(entry['username'])
       
    queryset2 = Customer.objects.values('is_active').annotate(population=Sum('is_active')).order_by('username')
    for entry in queryset2:
        data.append(entry['is_active'])
       
    return JsonResponse(data={
        'labels': labels,
        'data': data,
    })
    
    