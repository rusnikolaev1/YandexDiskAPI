from rest_framework import throttling


class GetRequestsRateThrottle(throttling.AnonRateThrottle):
    scope = "get_requests"


class PostDeleteRequestsRateThrottle(throttling.AnonRateThrottle):
    scope = "post_delete_requests"
