from django.shortcuts import render,get_object_or_404
from .models import Book
from category.models import Category
from checkout.models import order_list
from checkout.models import order
from checkout.models import invoice
from accounts.models  import Account
from checkout.models import invoice
from django.contrib import messages
from django.contrib.auth.decorators import  login_required
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
from django.db.models import Q
import requests
import json

categories_list = Category.objects.all()


#adding paging


def home(request):

    books = Book.objects.all()[0:20]
    categories= Category.objects.all()
    font_page_context = {
        'books': books,
        'categories': categories,
    }
    return render(request, 'index.html',font_page_context)




def members(request):

    accounts = Account.objects.all()[0:20]
    font_page_context = {
        'accounts': accounts,
    }
    return render(request, 'members.html',font_page_context)

def library(request,user_slug):

    print(user_slug)
    user= Account.objects.get(username=user_slug)
    books = Book.objects.filter(user__username=user_slug)
    font_page_context = {
        'books': books,
        'user': user
    }
    return render(request, 'library_public.html',font_page_context)



def contact(request):


    return render(request, 'contact-us.html')

def about(request):

    return render(request, 'about.html')

def single_book(request, single_book_slug):
    if single_book_slug is not None:
        book = get_object_or_404(Book,slug=single_book_slug)

        #releated_categories = get_object_or_404(Category,slug=single_book_slug)
        releated_books = Book.objects.all().filter(category=book.category)[0:5]
        context = {

            'book': book,
             'related_books': releated_books,

        }

    return render(request, 'book-single-page.html',context)


def search_result(request):
    print(request.GET)
    
    q = request.GET.get('query', '')
    books = Book.objects.filter(Q(title__icontains=q) | Q(author__icontains=q) | Q(description__icontains=q))
    print(q)
    print(books)
    context = {
        'books': books,
    }
    return render(request, 'search_res.html', context)


def save_book(request):
    if request.method == 'GET':
        
        data_book = request.GET

        image = request.FILES.get('image')
        
        
        print('image',image)
        thumbnail = data_book.get('thumbnail')
        if thumbnail is None:
            thumbnail = ''
        book = Book.objects.create(
            title=data_book.get('title'),
            author=data_book.get('authors'),
            image=image,
            price=data_book.get('price'),
            #publisher=data_book.get('publisher'),
            #publishedDate=data_book.get('publishedDate'),
            description=data_book.get('description'),
            number_pages=data_book.get('pageCount'),
            stocks=data_book.get('stocks'),
            category_id=1,
            user_id=1,
            slug=data_book.get('title'),
            image_google_api=thumbnail,
            #categories=data_book.get('categories'),
            #thumbnail=data_book.get('thumbnail'),
        )


        return render(request, 'send-book.html', {'book': book})
    else:
        return render(request, 'send-book.html')

def send_book(request):

    if request.method == 'GET':
        if request.method == 'GET':
            isbn = request.GET.get('isbn')
            if isbn:
                api_url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
                response = requests.get(api_url)
                if response.status_code == 200:
                    book_data = response.json()
                    if 'items' in book_data:
                        book_info = book_data['items'][0]['volumeInfo']
                        # Procesar los datos del libro según sea necesario

                        print(book_info)
                        context = {
                            'title': book_info.get('title'),
                            'authors': book_info.get('authors'),
                            'publisher': book_info.get('publisher'),
                            'publishedDate': book_info.get('publishedDate'),
                            'description': book_info.get('description'),
                            'pageCount': book_info.get('pageCount'),
                            'categories': book_info.get('categories'),
                            'thumbnail': book_info.get('thumbnail'),
                            'image':book_info.get('image'),
                            'image2':book_info.get('image2'),
                            'image3':book_info.get('image3'),
                            'image4':book_info.get('image4')
                        }
                        print(context)
                    else:
                        context = {'error': 'No se encontró información para el ISBN proporcionado.'}
                else:
                    context = {'error': 'Error al realizar la solicitud a la API.'}
            else:
                context = {'error': 'No se proporcionó un ISBN.'}
            print(context)
            return render(request, 'send-book.html', context)

@login_required(login_url="/login")
def orders(request):
        if request.user.is_authenticated:
            user = Account.objects.get(email=request.user.email)
            order_id = order.objects.all().filter(client=user).order_by('date_created')

            all_orders = Paginator(order.objects.all().filter(client=user).order_by('-date_created'), 10)
            page = request.GET.get('page')

            try:
                orders = all_orders.page(page)
            except PageNotAnInteger:
                orders = all_orders.page(1)
            except EmptyPage:
                orders=  all_orders.page(all_orders.num_pages)

            context={

                'order_id_list' : orders,
            }
            return render(request,"list-orders.html",context)
        else:
            messages.error("Sorry, you need to be logged in to view your orders")
            return redirect("login")

@login_required(login_url="/login")
def view_order(request, order_id):
      if request.user.is_authenticated:

          print(order_id)
          order_items_list = order_list.objects.all().filter(order_id=order_id)
          invoice_details = invoice.objects.all().filter(order_id=order_id)



          context={
              "order_id":order_id,

              "order_items_list":order_items_list,
              "invoice_list": invoice_details
          }
          return render(request,"view_order.html",context=context)
      else:
          return redirect('login')


@login_required(login_url="/login")
def view_invoice(request, invoice_id):
     if request.user.is_authenticated:
         invoice_dat = invoice.objects.get(invoice_id=invoice_id)

         context = {

             'invoice':invoice_dat

         }
         return render(request,"view_invoice.html",context=context)
     else:
         return redirect("login")




