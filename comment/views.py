import json
from operator         import itemgetter

from django.views     import View
from django.http      import JsonResponse
from django.db.models import Count

from .models          import Comment, Like
from movie.models     import Movie
from users.models     import User
from analysis.models  import Star
from users.utils      import login_decorator


class CommentView(View):
    @login_decorator
    def post(self, request):
        data = json.loads(request.body)

        try:
            movie_check = Movie.objects.filter(id = data["movieId"])
            star_check  = Star.objects.filter(
                user_id  = request.user.id,
                movie_id = data["movieId"]
            )

            if not movie_check.exists():
                return JsonResponse({"message": "NO_MOVIE"}, status=400)

            if not star_check.exists():
                return JsonResponse({"message":" NO_PERMISSION"}, status=403)

            comment_check = Comment.objects.filter(
                user_id  = request.user.id,
                movie_id = data["movieId"]
            )

            if comment_check.exists():
                return JsonResponse({"message": "ALREADY_EXIST"}, status=400)

            comment = Comment.objects.create(
                user_id    = request.user.id,
                movie_id   = data["movieId"],
                content    = data["content"]
            )

            comment.comment_id = comment.id
            comment.save()

            feedback = {
                "content" : comment.content
            }
            return JsonResponse(feedback, status=201)

        except KeyError:
            return jsonresponse({"message": "KEY_ERROR"}, status=400)

    @login_decorator
    def get(self, request, movie_id):
        movie_check = Movie.objects.filter(id=movie_id)

        if not movie_check.exists():
            return JsonResponse({"message": "NO_MOVIE"}, status=400)

        check_comment = Comment.objects.filter(
            user_id  = request.user.id,
            movie_id = movie_id
        )

        comment  = ''
        if check_comment.exists():
            comment = check_comment.first()
            comment = comment.content
        else:
            comment = ''

        feedback = {
            "content" : comment
        }
        return JsonResponse(feedback, status=200)

    @login_decorator
    def patch(self, request, movie_id):
        data = json.loads(request.body)

        try:
            movie_check = Movie.objects.filter(id=movie_id)

            if not movie_check.exists():
                return JsonResponse({"message": "NO_MOVIE"}, status=400)

            comment = Comment.objects.filter(
                user_id  = request.user.id,
                movie_id = movie_id
            )

            if comment.exists():
                comment         = comment.first()
                comment.content = data["content"]
                comment.save()
                update_comment  = comment.content
            else:
                return JsonResponse({"message": "NOT_FOUND"}, status=404)

            feedback = {
                "content"    : update_comment
            }
            return JsonResponse(feedback, status=200)

        except KeyError:
            return JsonResponse({"message": "KEY_ERROR"}, status=400)

    @login_decorator
    def delete(self, request, movie_id):
        movie_check = Movie.objects.filter(id=movie_id)

        comment = Comment.objects.filter(
            user_id  = request.user.id,
            movie_id = movie_id
        )

        if not movie_check.exists():
            return JsonResponse({"message": "NO_MOVIE"}, status=400)

        if not comment.exists():
            return JsonResponse({"message": "NOT_FOUND"}, status=404)

        comment.delete()

        feedback = {
            "message": "SUCCESS"
        }

        return JsonResponse(feedback, status=204)
      
      
class CommentListView(View):
    @login_decorator
    def get(self, request, movie_id):

        comments = Comment.objects.select_related(
            'user').prefetch_related('user__star_set',
                                     'like_set',
                                     'main_comment').filter(movie_id=movie_id)

        comment_list = [{
            "id"         : comment.id,
            "userName"   : comment.user.name,
            "userImage"  : comment.user.profile_image,
            "starPoint"  : comment.user.star_set.get(movie_id=movie_id).point,
            "content"    : comment.content,
            "likeCount"  : comment.like_set.count(),
            "replyCount" : comment.main_comment.count()-1,
        } for comment in comments if comment.id == comment.comment_id]

        ordered_list = sorted(comment_list, key=itemgetter("likeCount"), reverse=True)

        return JsonResponse({"data": ordered_list}, status=200)