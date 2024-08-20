from django.shortcuts import render,get_object_or_404
from .models import *
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
from django.http import JsonResponse
import json
import re
import csv
from bs4 import BeautifulSoup
from lxml import etree
from django.shortcuts import redirect



categories_list = Category.objects.all()


#adding paging

def getInfoBookGoogleApi(isbn):
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}&langRestrict=es"   
    print(url)
    response = requests.get(url)
    books = []
    if response.status_code == 200:
        data = response.json()
        
        
        for item in data.get('items', []):
            book_info = item.get('volumeInfo', {})
            
            books.append({
                'title': book_info.get('title'),
                'authors': book_info.get('authors', []),
                'publisher': book_info.get('publisher'),
                'published_date': book_info.get('publishedDate'),
                'description': book_info.get('description', 'No description available'),
                'categories': book_info.get('categories', []),
                'categories_list': book_info.get('categories', []),
                'thumbnail': book_info.get('imageLinks', {}).get('thumbnail'),
                'infoLink': book_info.get('infoLink'),
                'origen': 'google'
            })
    return books

def getInfoBookOpenLibraryApi(isbn):
    query_params = {}
    query_params['limit'] = 10
    query_params['language'] = 'spa'
    books=[]
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    response = requests.get(url, params=query_params)
    if response.status_code == 200:
        data = response.json()
        book_data = data.get(f'ISBN:{isbn}', {})
        
        if book_data:
            print('Encuentra libro en open library')
            book_info = {
                'title': book_data.get('title', 'No title available'),
                'authors': [author.get('name') for author in book_data.get('authors', [])],
                'publisher': [publisher.get('name') for publisher in book_data.get('publishers', [])],
                'published_date': book_data.get('publish_date', 'No publish date available'),
                'description': book_data.get('notes', 'No description available'),
                'categories_list': book_data.get('subjects', []),
                'thumbnail': book_data.get('cover', {}),
                'key': book_data.get('url', None),
                'origen': 'openlibrary'
            }
            books.append(book_info)
    return books


def import_books_open_library(request,author):
    
    publisher_name = request.GET.get('publisher_name', '')
    title = request.GET.get('title', '')
    #author = request.GET.get('author', '')
    
    
    # Construct the query parameters
    query_params = {}
    if publisher_name:
        query_params['publisher'] = publisher_name
    if title:
        query_params['title'] = title
    if author:
        query_params['author'] = author
    
    # URL for Open Library API to fetch books
    query_params['limit'] = 10
    query_params['language'] = 'spa'
    url = "https://openlibrary.org/search.json"
    response = requests.get(url, params=query_params)

    
    if response.status_code == 200:
        data = response.json()
        books = []
        
        for item in data.get('docs', []):
            print(item)
            books.append({
                'title': item.get('title'),
                'author_name': item.get('author_name', []),
                'publisher': item.get('publisher', ''),
                'publish_date': item.get('publish_date', ''),
                'isbn': item.get('isbn', []),
                'description': item.get('description', 'No description available'),
                'reviews': item.get('reviews', []),
                'cover_i': f"http://covers.openlibrary.org/b/id/{item.get('cover_i')}-L.jpg" if item.get('cover_i') else None,
                'key': f"https://openlibrary.org{item.get('key')}",
            })
        
        return JsonResponse({'books': books})
    else:
        return JsonResponse({'error': 'Failed to fetch data from Open Library API'}, status=response.status_code)


def import_by_isbn(isbn):

    isbn = isbn.replace('-', '')
    isbn = isbn.replace(' ', '')
    print(isbn)
    books=getInfoBookOpenLibraryApi(isbn)
    if len(books) == 0:
        books=getInfoBookGoogleApi(isbn)

    if len(books) > 0:
        print(books)
        index_book=0
        image = books[index_book]['thumbnail']
        if image is None:
            image = 'https://via.placeholder.com/150'
        else:
            if books[index_book]['origen'] == 'openlibrary':
                if 'large' in image:
                    image = image['large']
                pass
        slug = re.sub(r'[^\w\s-]', '', books[index_book]['title']).strip().replace(' ', '-').lower()
        slug = slug.replace('ñ', 'n').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')

        try:
            # Rest of the code...
            if BookTemplate.objects.filter(isbn=isbn).exists():
                print('Book already exists')
                BookTemplate.objects.filter(isbn=isbn).update(published_date=books[index_book]['published_date'],publisher=books[index_book]['publisher'],origen=books[index_book]['origen'],slug=slug, categories_list=books[index_book]['categories_list'], isbn=isbn, title=books[index_book]['title'], author=books[index_book]['authors'][0], description=books[index_book]['description'], image_google_api=image)
            else:
                print('Save book')
                BookTemplate(published_date=books[index_book]['published_date'],publisher=books[index_book]['publisher'],origen=books[index_book]['origen'],slug=slug, categories_list=books[index_book]['categories_list'], isbn=isbn, title=books[index_book]['title'], author=books[index_book]['authors'][0], description=books[index_book]['description'], image_google_api=image).save()
        except Exception as e:
            print('Error saving book', e)
                
    else:
        print('No books found')
    
    
    
    return 'ok'

def extrae_link(url):
    request = requests.get(url)
    soup = BeautifulSoup(request.text, 'html.parser')
    dom = etree.HTML(str(soup))
    # Extraer todos los elementos que tienen la clase "product photo product-item-photo"
    
    elements = dom.xpath('//*[contains(@class, "product photo product-item-photo")]')
    for element in elements:
        # Renderizar el contenido del elemento
        element_html = etree.tostring(element, pretty_print=True).decode()
        soup = BeautifulSoup(element_html, 'html.parser')
        image_element = soup.select_one('.product-image-photo')
        if image_element:
            image_url = image_element['src']
            print('image_url:', image_url)
                    
        url = element.get('href')
        request = requests.get(url)
        soup = BeautifulSoup(request.text, 'html.parser')
        dom = etree.HTML(str(soup))
        
       
      
        element=dom.xpath('//*[@id="description"]/div/div')
        if element:
            description = element[0].text.strip()
        else:
            description = ''
        print('description',description)
        
        element = dom.xpath('//*[@id="maincontent"]/div[2]/div/div[1]/div[2]/div[1]/h1/span')
        print('titulo',element[0].text.strip())
        titulo=element[0].text.strip()
        element=dom.xpath('//*[@id="maincontent"]/div[2]/div/div[1]/div[2]/div[1]/a')
        if element:
            autor = element[0].text.strip()
        else:
            autor = ''
        element=dom.xpath('//*[@id="product-attribute-specs-table"]/tbody/tr[1]/td')
        print('isbn',element[0].text.strip())
        isbn=element[0].text.strip()
        element=dom.xpath('//*[@id="product-attribute-specs-table"]/tbody/tr[3]/td')
        print('publisher',element[0].text.strip())
        publisher=element[0].text.strip()
        element=dom.xpath('//*[@id="product-attribute-specs-table"]/tbody/tr[4]/td')
        print('lenguaje',element[0].text.strip())
        language=element[0].text.strip()
        element=dom.xpath('//*[@id="product-attribute-specs-table"]/tbody/tr[6]/td')
        if element:
            published_date=element[0].text.strip()
        else:
            published_date=''
        element=dom.xpath('//*[@id="product-attribute-specs-table"]/tbody/tr[7]/td')
        if len(element)>0:
            number_pages=element[0].text.strip()
        else:    
            number_pages=''
        
        slug = re.sub(r'[^\w\s-]', '', titulo).strip().replace(' ', '-').lower()
        slug=slug.replace('ñ','n').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')
        # Guarda en BookTemplate la info extraida
        # 
        if BookTemplate.objects.filter(isbn=isbn).exists():
            print('Book already exists')
            BookTemplate.objects.filter(isbn=isbn).update(slug=slug,published_date=published_date,publisher=publisher,language=language,description=description,number_pages=number_pages,image_google_api=image_url)   
        else:
            try:
                BookTemplate.objects.create(
                    slug=slug,
                    title=titulo,
                    author=autor,
                    isbn=isbn,
                    publisher=publisher,
                    language=language,
                    published_date=published_date,
                    number_pages=number_pages,
                    description=description,
                    image_google_api=image_url
                )
            except Exception as e:
                print('Error saving book', e)

    
    '''
    
    isbn='9788497596820, 9788497596837, 9788497596844, 9788497596851, 9788499082901, 9788499082925, 9788499082932, 9788499082949, 9788499082956, 9788499082963, 9788499082970, 9788499082987, 9788499082994, 9788499083007, 9788499083014, 9788499083021, 9788499083038, 9788499083045, 9788499083052, 9788499083069, 9788499083076, 9788499083083, 9788499083090, 9788499083106, 9788499083113, 9788499083120, 9788499083137, 9788499083144, 9788499083151, 9788499083168, 9788499083175, 9788499083182, 9788499083199, 9788499083205, 9788499083212, 9788499083229, 9788499083236, 9788499083243, 9788499083250, 9788499083267, 9788499083274, 9788499083281, 9788499083298, 9788499083304, 9788499083311, 9788499083328, 9788499083335, 9788499083342, 9788499083359'
    isbn='9786124442520'
    isbn_list = isbn.split(',')
    for isbn in isbn_list:
        import_by_isbn(isbn)
    
    
    books=BookTemplate.objects.all()
    for book in books:
        print(book.title)
        import_by_isbn(book.isbn)
    return render(request, 'import_books.html')
    
    '''
def import_books(request):

    url_base='https://www.sbs.com.pe/catalogsearch/result/?q=Penguin+cl%C3%A1sicos'

    
    i=0   
    for i in range(0, 10):
        i=i+1
        url=url_base+'?p='+str(i)
        url=f"https://www.sbs.com.pe/catalogsearch/result/index/?p={i}&q=Penguin+cl%C3%A1sicos"

        print(url)
        extrae_link(url)
        print('-------------------------------')

    JsonResponse({'url': url})


def import_casa_libros(link):
    url='https://www.casadellibro.com.co/libros/arte/cine/101004000'
    request = requests.get(url)
    soup = BeautifulSoup(request.text, 'html.parser')
    dom = etree.HTML(str(soup))
    elements = dom.xpath('//*[contains(@class, "compact-product")]')
    
    for element in elements:
        # Renderizar el contenido del elemento
        element_html = etree.tostring(element, pretty_print=True).decode()
        soup = BeautifulSoup(element_html, 'html.parser')
        print(soup)
    return 'ok'


def home(request):

    books = BookTemplate.objects.all().order_by('-created_on')

    categories= Category.objects.all()
    font_page_context = {
        'books': books,
        'categories': categories,
        'books_ihave': Book.objects.filter(ihave=True,user_id=request.user.id),
        'books_iloveyou': Book.objects.filter(iloveyou=True,user_id=request.user.id),
        'books_iwish': Book.objects.filter(iwish=True,user_id=request.user.id),
    }
    return render(request, 'index.html',font_page_context)

def add_lo_quiero(request, isbn):
    try:
        book_template = BookTemplate.objects.get(isbn=isbn)
        if book_template is None:
            return redirect('/book/'+book_template.slug)
            #return JsonResponse({'error': 'BookTemplate with given ISBN does not exist'}, status=404)
        if Book.objects.filter(book_id=book_template.id).count() > 0:
            Book.objects.filter(book_id=book_template.id).update(iwish=True)
            return redirect('/book/'+book_template.slug)
        book = Book.objects.create(
            title=book_template.title,
            author=book_template.author,
            image_google_api=book_template.image_google_api,
            price=0,
            description=book_template.description,
            number_pages=book_template.number_pages,
            stocks=1,
            category_id=1,
            user_id=request.user.id,
            slug=book_template.slug,
            book_id=book_template.id,
            iwish=True
        )
        
        return redirect('/book/'+book.slug)
        
        #return JsonResponse({'message': 'Book added successfully'})
    except BookTemplate.DoesNotExist:
        return JsonResponse({'error': 'BookTemplate with given ISBN does not exist'}, status=404)
    except Exception as e:
        
        return JsonResponse({'error': 'Failed to add book', 'details': str(e)}, status=500)

def add_iloveyou(request, isbn):
    try:
        book_template = BookTemplate.objects.get(isbn=isbn)
        if book_template is None:
            return JsonResponse({'error': 'BookTemplate with given ISBN does not exist'}, status=404)
        if Book.objects.filter(book_id=book_template.id).count() > 0:
            Book.objects.filter(book_id=book_template.id).update(iloveyou=True)
            return JsonResponse({'error': 'Book already added'}, status=400)
        book = Book.objects.create(
            title=book_template.title,
            author=book_template.author,
            image_google_api=book_template.image_google_api,
            price=0,
            description=book_template.description,
            number_pages=book_template.number_pages,
            stocks=1,
            category_id=1,
            user_id=request.user.id,
            slug=book_template.slug,
            book_id=book_template.id,
            iloveyou=True
        )
        return JsonResponse({'message': 'Book added successfully'})
    except BookTemplate.DoesNotExist:
        return JsonResponse({'error': 'BookTemplate with given ISBN does not exist'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Failed to add book', 'details': str(e)}, status=500)

def add_ihave(request, isbn):
    try:
        book_template = BookTemplate.objects.get(isbn=isbn)
        if book_template is None:
            return JsonResponse({'error': 'BookTemplate with given ISBN does not exist'}, status=404)
        if Book.objects.filter(book_id=book_template.id).count() > 0:
            Book.objects.filter(book_id=book_template.id).update(ihave=True)
            return JsonResponse({'error': 'Book already added'}, status=400)
        book = Book.objects.create(
            title=book_template.title,
            author=book_template.author,
            image_google_api=book_template.image_google_api,
            price=0,
            description=book_template.description,
            number_pages=book_template.number_pages,
            stocks=1,
            category_id=1,
            user_id=request.user.id,
            slug=book_template.slug,
            book_id=book_template.id,
            ihave=True
        )
        return JsonResponse({'message': 'Book added successfully'})
    except BookTemplate.DoesNotExist:
        return JsonResponse({'error': 'BookTemplate with given ISBN does not exist'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Failed to add book', 'details': str(e)}, status=500)



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
        'user': user,
        'books_ihave': Book.objects.filter(ihave=True,user_id=user.id),
        'books_iloveyou': Book.objects.filter(iloveyou=True,user_id=user.id),
        'books_iwish': Book.objects.filter(iwish=True,user_id=user.id),
    }
    return render(request, 'library_public.html',font_page_context)



def contact(request):


    return render(request, 'contact-us.html')

def about(request):

    return render(request, 'about.html')

def single_book(request, single_book_slug):
    if single_book_slug is not None:
        booktemplate = get_object_or_404(BookTemplate,slug=single_book_slug)
        users_id=Book.objects.filter(book_id=booktemplate.id).values_list('user_id', flat=True)
        accounts = Account.objects.filter(id__in=users_id)

        #releated_categories = get_object_or_404(Category,slug=single_book_slug)
        #releated_books = Book.objects.all().filter(category=book.category)[0:5]
        context = {

            'book': booktemplate,
            'related_books': {},
            'accounts': accounts

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




