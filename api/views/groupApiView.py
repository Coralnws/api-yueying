from asyncio.windows_events import NULL
import operator
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from rest_framework.response import Response
from rest_framework import generics, status, permissions
from drf_yasg.utils import swagger_auto_schema

from ..serializers.groupSerializers import *
from ..serializers.groupRelationsSerializers import *
from ..serializers.feedSerializers import *
from ..serializers.userSerializers import *
from ..utils import *
from ..models.groups import Group
from ..models.userRelations import *
from ..models.feeds import *
from ..models.reviews import *
from ..models.groupRelations import *
from ..api_throttles import *

"""
GET : Get a group by Id
PUT: Update Group By Id 
DELETE: Delete Group By Id
"""
class GroupDetailView(generics.GenericAPIView):
    serializer_class = GroupDetailSerializer
    permissions_classes = [permissions.IsAuthenticatedOrReadOnly]
    throttle_classes = [anonRelaxed, userRelaxed]

    def get_serializer_class(self):
        if self.request.method in ['GET']:
            return GroupProfileSerializer
        return GroupDetailSerializer

    # Get Group Detail By Id
    @swagger_auto_schema(operation_summary="Get Group Detail By Id")
    def get(self, request, groupId):
        try:
            group = get_object_or_404(Group, pk=groupId)
            members = UserGroup.objects.filter(group=groupId,isBanned=False).count()
            group.members = members
            owner = CustomUser.objects.filter(pk=group.createdBy.id).first()
            group.owner = owner.username
            serializer = self.get_serializer(instance=group)
            data = serializer.data
            data['message'] = "Get Group Detail Successfully"
            return Response(data, status=status.HTTP_200_OK)

        except:
            return Response({"message": "Get Group Detail Failed"}, status=status.HTTP_400_BAD_REQUEST)

    # Update Group By Id
    @swagger_auto_schema(operation_summary="Update Group By Id")
    def put(self, request, groupId):
        try:
            member = UserGroup.objects.get(group=groupId, user=request.user)
            if member.isAdmin or member.isMainAdmin:
                group = get_object_or_404(Group, pk=groupId)
                serializer = self.get_serializer(instance=group, data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save(updatedAt=timezone.now())
                data = serializer.data
                data['message'] = "Update Group Successfully"
                return Response(data, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Not Group Admin"},  status=status.HTTP_401_UNAUTHORIZED)
                
        except:
            return Response({"message": "Update Group Failed,Not Group Member"}, status=status.HTTP_400_BAD_REQUEST)

    # Delete Group By Id
    @swagger_auto_schema(operation_summary="Delete Group By Id")
    def delete(self, request, groupId):
        isMainAdmin = UserGroup.objects.get(group=groupId, user=request.user, isMainAdmin=True)
        if isMainAdmin:
            try:
                group = get_object_or_404(Group, pk=groupId)
                group.delete()
                return Response({"message": "Delete Group Successfully"}, status=status.HTTP_200_OK)
            except:
                return Response({"message": "Delete Group Failed,Probably Not Group Creator"}, status=status.HTTP_400_BAD_REQUEST)

'''
POST:Create Group
'''
class GroupCreateView(generics.CreateAPIView):
    serializer_class = GroupCreateSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    throttle_classes = [anonRelaxed, userRelaxed]

    @swagger_auto_schema(operation_summary="Create Group")
    def post(self, request):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(createdBy=user)

        #add newUserGroup
        group = get_object_or_404(Group, pk=serializer.data["id"])
        newUsergroup = UserGroup(group=group, user=request.user,isMainAdmin=True)
        newUsergroup.save()
        data = serializer.data
        data['message'] = "Create Group Successfully"
        return Response(data, status=status.HTTP_201_CREATED)


'''
POST/DELETE: Join and leave group
'''
class JoinLeaveGroupView(generics.GenericAPIView):
    serializer_class = UserGroupJoinSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    throttle_classes = [anonRelaxed, userRelaxed]

    @swagger_auto_schema(operation_summary="Join Group")
    def post(self,request,groupId):
        try:
            group = get_object_or_404(Group, pk=groupId)
            member = UserGroup.objects.filter(group=group, user=request.user)
            if member:
                return Response({"message": "User already join the group"}, status=status.HTTP_403_FORBIDDEN)
            data = {'user':request.user.id,'group':group.id}
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            data = serializer.data
            data['message'] = "Join Group Successfully"
            return Response(data, status=status.HTTP_201_CREATED)
        except:
            return Response({"message": "Join Group Failed"}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(operation_summary="Leave Group, Cannot Leave If isBanned")
    def delete(self, request, groupId):
        isMember = UserGroup.objects.get(group=groupId, user=request.user)
        if isMember:
            if not isMember.isMainAdmin:
                if isMember.isBanned:
                    if isMember.banDue > timezone.now():
                        return Response({"message": "Leave Group Failed, You Are Banned From This Action"}, status=status.HTTP_403_FORBIDDEN)
                    # If bandue is now, set isBanned to false
                    isMember.isBanned = False
                isMember.delete()
                return Response({"message": "Leave Group Successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Leave Group Failed, You Are Main Admin Of The Group"}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({"message": "Leave Group Failed, Not Group Member"}, status=status.HTTP_401_UNAUTHORIZED)

#################################### For members ####################################

'''
POST: Create Feed in Group
'''
class GroupFeedCreateView(generics.CreateAPIView):
    serializer_class = FeedCreateSerializer
    throttle_classes = [anonRelaxed, userRelaxed]

    @swagger_auto_schema(operation_summary="Create Feed In Group, Cannot Create If isBanned")
    def post(self,request,groupId):
        isMember = UserGroup.objects.get(group=groupId, user=request.user)
        if isMember:
            if isMember.isBanned and not isMember.isMainAdmin:
                if isMember.banDue > timezone.now():
                    return Response({"message": "Post Feed in Group Failed, You Are Banned From This Action"}, status=status.HTTP_403_FORBIDDEN)
                # If bandue is now, set isBanned to fals
                isMember.isBanned = False
            group = get_object_or_404(Group, pk=groupId)
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(createdBy=request.user, isPublic=False ,belongTo=group)

            # add GroupFeed
            group = Group.objects.get(pk=groupId)
            feed = Feed.objects.get(pk=serializer.data["id"])
            Groupfeed = GroupFeed(group=group, feed=feed)
            Groupfeed.save()
            data = serializer.data

            #add UserFeed
            feed = Feed.objects.get(pk=serializer.data["id"])
            userFeed = UserFeed(feed=feed,user=request.user)
            userFeed.save()

            data['message'] = "Create Feed Successfully"
            return Response(data, status=status.HTTP_201_CREATED)
        return Response({"message": "Not Group Member."}, status=status.HTTP_401_UNAUTHORIZED)


'''
POST:Request Group Admin 
'''
class GroupAdminRequestView(generics.CreateAPIView):
    serializer_class = AdminRequestSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    throttle_classes = [anonRelaxed, userRelaxed]

    @swagger_auto_schema(operation_summary="Request For Group Admin Role")
    def post(self,request,groupId):
        user = request.user
        isMember = UserGroup.objects.filter(group=groupId, user=user, isAdmin=False,isMainAdmin=False).first()
        if isMember:
            if isMember.isBanned and not isMember.isMainAdmin:
                if isMember.banDue > timezone.now():
                    return Response({"message": "Request Group Admin Failed, You Are Banned From This Action"}, status=status.HTTP_403_FORBIDDEN)
                # If bandue is now, set isBanned to fals
                isMember.isBanned = False
            record = GroupAdminRequest.objects.filter(group=groupId, user=user).first()
            data = {'user':user.id,'group':groupId,'result':0}
            if record:
                serializer = self.get_serializer(instance=record,data=data)
            else:
                serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save(updatedAt=timezone.now())
            data = serializer.data
            data['message'] = "Apply Group Admin Successfully"
            return Response(data, status=status.HTTP_200_OK)
        return Response({"message": "Apply group admin Failed, Not Group Member or Is Admin Already"}, status=status.HTTP_401_UNAUTHORIZED)

################################ Show ######################################
### Outside ###
'''
GET: Sort by Category (members in descending order)
'''
class GroupbyCategoryView(generics.ListAPIView):
    serializer_class = ListGroupSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    throttle_classes = [anonRelaxed, userRelaxed]

    @swagger_auto_schema(operation_summary="Get All Groups By Category")
    def get_queryset(self):
        type = self.kwargs['category']
        allGroups = Group.objects.filter(category=type)
        for group in allGroups:
            members = UserGroup.objects.filter(group=group,isBanned=False).count()
            group.members = members
        ordered = sorted(allGroups, key=operator.attrgetter('members'), reverse=True)
        return ordered

'''
GET: Show group join by user
'''
class ShowUserGroupView(generics.ListAPIView):
    serializer_class = ListGroupSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    throttle_classes = [anonRelaxed, userRelaxed]

    @swagger_auto_schema(operation_summary="Get All Group Joined By User")
    def get_queryset(self):
        allGroups = Group.objects.filter(usergroup__user=self.request.user)
        for group in allGroups:
            owner = CustomUser.objects.filter(pk=group.createdBy.id).first()
            group.owner = owner.username
            members = UserGroup.objects.filter(group=group,isBanned=False).count()
            group.members = members
        ordered = sorted(allGroups, key=operator.attrgetter('members'), reverse=True)
        return ordered


### Inside Group ###
'''
GET : Show/Search Group Feed
'''
class GroupFeedListView(generics.ListAPIView):
    serializer_class = ListGroupFeedSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    throttle_classes = [anonRelaxed, userRelaxed]

    # Get All Group Feeds
    @swagger_auto_schema(operation_summary="Get All Group Feeds")
    def get_queryset(self):
        group = self.kwargs['groupId']
        category = self.request.GET.get('category')
        search = self.request.GET.get('search')
        searchName = self.request.GET.get('searchName')

        filter = Q()
        filter &= Q(isPublic=False, belongTo=group, groupfeed__group=group)

        if search is not None:
            searchTerms = search.split(' ')
            for term in searchTerms:
                filter &= Q(title__icontains=term) | Q(description__icontains=term) | Q(createdBy__username__icontains=term)
        
        if searchName is not None:
            searchTerms = searchName.split(' ')
            for term in searchTerms:
                filter &= Q(title__icontains=term)
        
        if category == 'p':
            filter &= Q(groupfeed__isPin=True)
        elif category == 'f':
            filter &= Q(groupfeed__isFeatured=True)
        elif category == 'n':
            filter &= Q(groupfeed__isPin=False, groupfeed__isFeatured=False)

        allFeeds = Feed.objects.filter(filter)
        for feed in allFeeds:
            feedType = GroupFeed.objects.filter(feed=feed).first()
            allUserFeeds = UserFeed.objects.filter(feed=feed)
            reviewers = Review.objects.filter(feed=feed).count()
            likes = allUserFeeds.filter(response='L').count()
            dislikes = allUserFeeds.filter(response='D').count()
            feed.likes = likes
            feed.dislikes = dislikes
            feed.reviewers = reviewers
            feed.response = 'O'

            if feedType.isPin:
                feed.isPin = 1
            else:
                feed.isPin = 0
            if feedType.isFeatured:
                feed.isFeatured = 1
            else:
                feed.isFeatured = 0

            if not self.request.user.is_anonymous:
                userfeed = UserFeed.objects.filter(user=self.request.user,feed=feed).first()
                if userfeed:
                    if userfeed.response == 'L':
                        feed.response = 'L'
                    if userfeed.response == 'D':
                        feed.response = 'D'

                    
        ordered = sorted(allFeeds, key=operator.attrgetter('isPin','createdAt'),reverse=True)
        return ordered

################################ Query ######################################
'''
GET:Show/Search Group
'''
class GroupListView(generics.ListAPIView):
    serializer_class = ListGroupSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    throttle_classes = [anonRelaxed, userRelaxed]

    # Get All Groups
    @swagger_auto_schema(operation_summary="Get All Groups")
    def get_queryset(self):
        #orderBy = self.request.GET.get('orderBy')
        search = self.request.GET.get('search')
        searchName = self.request.GET.get('searchName')
        category = self.request.GET.get('category')

        filter = Q()
        if search is not None:
            searchTerms = search.split(' ')
            for term in searchTerms:
                filter |= Q(groupName__icontains=term) | Q(description__icontains=term) | Q(createdBy__username__icontains=term)

        if searchName is not None:
            searchTerms = searchName.split(' ')
            for term in searchTerms:
                filter &= Q(groupName__icontains=term)

        if category is not None:
            filter &= Q(category=category)

        allGroups = Group.objects.filter(filter)
        for group in allGroups:
            owner = CustomUser.objects.filter(pk=group.createdBy.id).first()
            group.owner = owner.username
            members = UserGroup.objects.filter(group=group,isBanned=False).count()
            group.members = members
        ordered = sorted(allGroups, key=operator.attrgetter('members'), reverse=True)
        return ordered

'''
GET:Show Member 
'''
class GroupMemberView(generics.ListAPIView):
    serializer_class = ListMemberSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    throttle_classes = [anonRelaxed, userRelaxed]

    @swagger_auto_schema(operation_summary="Get All Group Members In A Group")
    def get_queryset(self):
        group = self.kwargs['groupId']
        search = self.request.GET.get('search')
        role = self.request.GET.get('role')
        isBan = self.request.GET.get('isBan')
        # 1=mainAdmin , 2=Admin ,3=normal member

        allBannedMember = UserGroup.objects.filter(group=group, isBanned=True)
        for member in allBannedMember:
            if member.isBanned and member.banDue < timezone.now():
                member.isBanned=False
                member.save()

        filter = Q()
        filter &= Q(usergroup__group=group,)

        if search is not None:
            searchTerms = search.split(' ')
            for term in searchTerms:
                filter &= Q(username__icontains=term)
        
        if role == '1':
            filter &= Q(usergroup__isMainAdmin=True)
        elif role == '2':
            filter &= Q(usergroup__isAdmin=True)
        elif role == '3':
            filter &= Q(usergroup__isAdmin=False,usergroup__isMainAdmin=False)

        if isBan == "True":
            filter &= Q(usergroup__isBanned=True)
        else:
            filter &= Q(usergroup__isBanned=False)

        allMember = CustomUser.objects.filter(filter)
        for member in allMember:
            member.isMainAdmin = False
            member.isAdmin = False
            member.isNormal = False
            member.isBanned = False
            type = UserGroup.objects.filter(user=member, group=group).first()
            if type.isMainAdmin:
                member.isMainAdmin = True
            if type.isAdmin:
                member.isAdmin = True
            else:
                member.isNormal = True
            if type.isBanned:
                member.isBanned = True

        return allMember


'''
GET:Show All Admin Request（All result）
'''
class ShowRequestView(generics.ListAPIView):
    serializer_class = AdminRequestSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    throttle_classes = [anonRelaxed, userRelaxed]

    @swagger_auto_schema(operation_summary="Get All Admin Requests")
    def get_queryset(self):
        group = self.kwargs['groupId']
        search = self.request.GET.get('search')
        result = self.request.GET.get('result')
        isAdmin = UserGroup.objects.get(group=group, user=self.request.user, isAdmin=True)
        if isAdmin:
            filter = Q()
            if search is not None:
                searchTerms = search.split(' ')
                for term in searchTerms:
                    filter &= Q(user__username__icontains=term) | Q(group__groupName__icontains=term)
            if result is None:
                result = 0
            filter &= Q(result=result, group=group)

            allRequest = GroupAdminRequest.objects.filter(filter)
            return allRequest
        return Response({"message": "Unauthorized for getting admin request report"}, status=status.HTTP_401_UNAUTHORIZED)

'''
GET:Show User Who Have Pending Admin Request
'''
class ShowRequestUserView(generics.ListAPIView):
    serializer_class = ListUserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    throttle_classes = [anonRelaxed, userRelaxed]

    @swagger_auto_schema(operation_summary="Get User With Pending Admin Request")
    def get_queryset(self):
        group = self.kwargs['groupId']
        allBannedMember = UserGroup.objects.filter(group=group, isBanned=True)
        for member in allBannedMember:
            if member.isBanned and member.banDue < timezone.now():
                member.isBanned=False
                member.save()

        allUser = CustomUser.objects.filter(usergroup__group=group,usergroup__isBanned=False,groupadminrequest__result=0,groupadminrequest__group=group)

        return allUser