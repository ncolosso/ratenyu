import logging
from json import dumps
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from courses.models import Review
from professors.models import Professor
from .course_util import *
from util.views import error404

LOGGER = logging.getLogger("project")


def course_detail(request: HttpRequest, course_id: str):
    LOGGER.debug(f"course_detail: {course_id}")
    try:
        if request.method == "GET":
            return load_course_detail(request, course_id)
        elif request.method == "POST" and "submit" in request.POST:
            LOGGER.debug(request.POST)
            review, message = add_review_from_details(request)
            return load_course_detail(request, course_id, review, message)
        else:
            LOGGER.error(request.POST)
            return error404(request, error="Invalid request")
    except Exception as e:
        return error404(request, error=e)


def load_course_detail(
    request: HttpRequest, course_id: str, review: bool = None, review_message: str = ""
) -> HttpResponse:
    try:
        course = Course.objects.get(course_id=course_id)
        classes = Class.objects.filter(course=course)
        professors_list = [cl.professor for cl in classes]
        reviews_list = create_review_objects(classes)
        reviews_avg = calculate_rating_avg(reviews_list)
        if review is not None:
            context = {
                "classes": classes,
                "course": course,
                "reviews_list": reviews_list,
                "reviews_avg": reviews_avg,
                "professors_list": professors_list,
                "review_saved": review,
                "review_message": review_message,
            }
        else:
            context = {
                "classes": classes,
                "course": course,
                "reviews_list": reviews_list,
                "reviews_avg": reviews_avg,
                "professors_list": professors_list,
            }
        LOGGER.debug(context)
        return render(request, "courses/detail.html", context)
    except Exception as e:
        return error404(request, error=e)


def add_review(request):
    context = {
        "courses": Course.objects.all(),
        "professors": Professor.objects.only("professor_id", "name"),
        "course_ids": [f"{course.course_subject_code} {course.catalog_number}" for course in Course.objects.all()],
        "courses_json": get_courses_data_json(),
        "professors_json": get_professors_data_json()
    }
    if request.method == "GET":
        if request.user.id is None:
            return redirect(reverse("search:index"))
        return render(request, "courses/add_review.html", context)
    elif request.method == "POST":
        user = User.objects.get(username=request.user)
        try:
            if not text_is_valid(request.POST["review_text"]):
                context["review_text_invalid"] = True
                add_redirect_message(
                    request=request,
                    message="Review not saved. Review text failed to meet RateNYU standards.",
                    success=False,
                )
                return redirect("courses:add_review")

            new_review = save_new_review(
                user=user,
                user_entered_course_id=request.POST["add_review_course_id"],
                professor_name=request.POST["add_review_professor_name"],
                review_rating=request.POST["review_rating"],
                review_text=request.POST["review_text"],
            )
            LOGGER.info(f"Created new Review: {new_review}")
            add_redirect_message(
                request=request,
                message="Your review was saved!",
                success=True,
            )
            return redirect("courses:add_review")
        except Exception as e:
            LOGGER.exception(f"Could not create review, encountered error: {e}")
            add_redirect_message(
                request=request,
                message="Uh Oh, something went wrong. Your review could not be saved.",
                success=False,
            )
            return redirect("courses:add_review")


def delete_review(request, review_id: str):
    try:
        r = Review.objects.get(pk=review_id)
        r.delete()
        add_redirect_message(
            request=request, message="Your review was deleted.", success=True
        )
        return redirect("users:profile", user_name=request.user)
    except Exception as e:
        return error404(request, error=e)
def edit_review(request):
    if request.method == 'POST':
        r = Review.objects.get(pk=request.POST.get('review_id'))
        r.review_text = request.POST.get('new_review_text')
        r.rating = request.POST['review_rating']
        r.save()
    return redirect('users:profile', user_name=request.user)
      


