from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.db.models import OuterRef, Subquery
from apps.messaging.models import Conversation, Message
from apps.messaging.forms import MessageForm
from apps.accounts.models import Notification


@login_required
def conversation_list(request):
    if request.user.acting_as_client():
        conversations = Conversation.objects.filter(client=request.user)
        base_template = 'base_client.html'
    else:
        conversations = Conversation.objects.filter(tasker=request.user)
        base_template = 'base_tasker.html'

    latest_msg = Message.objects.filter(conversation=OuterRef('pk')).order_by('-created_at')
    conversations = conversations.select_related(
        'client', 'tasker'
    ).annotate(
        last_msg_content=Subquery(latest_msg.values('content')[:1]),
        last_msg_sender_name=Subquery(latest_msg.values('sender__full_name')[:1]),
        last_msg_is_system=Subquery(latest_msg.values('is_system')[:1]),
        last_msg_created_at=Subquery(latest_msg.values('created_at')[:1]),
    ).order_by('-last_activity_at')

    return render(request, 'messaging/conversation_list.html', {
        'conversations': conversations,
        'base_template': base_template,
    })


@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.user not in conversation.participants():
        return HttpResponseForbidden(_('Vous n\'avez pas accès à cette conversation.'))

    if request.user == conversation.client:
        base_template = 'base_client.html'
    else:
        base_template = 'base_tasker.html'

    message_list = conversation.messages.all().order_by('created_at')

    Message.objects.filter(
        conversation=conversation,
        is_read=False,
    ).exclude(sender=request.user).update(is_read=True)

    Notification.objects.filter(
        user=request.user,
        type=Notification.TypeChoices.MESSAGE_RECEIVED,
        related_conversation=conversation,
        is_read=False,
    ).update(is_read=True)

    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            if message.file:
                message.file_name = message.file.name
            message.save()
            conversation.save(update_fields=['last_activity_at'])

            recipient = conversation.other_participant(request.user)
            Notification.objects.create(
                user=recipient,
                type=Notification.TypeChoices.MESSAGE_RECEIVED,
                title=_('Nouveau message'),
                message=_('Vous avez reçu un nouveau message de la part de %(sender)s.') % {
                    'sender': request.user.full_name,
                },
                related_conversation=conversation,
            )

            if request.htmx:
                return render(request, 'messaging/snippets/message_bubble.html', {
                    'message': message, 'request_user': request.user,
                })

            return redirect('messaging:conversation_detail', conversation_id=conversation.id)
        elif request.htmx:
            return HttpResponse('', status=400)
    else:
        form = MessageForm()

    return render(request, 'messaging/conversation_detail.html', {
        'conversation': conversation,
        'chat_messages': message_list,
        'form': form,
        'other_user': conversation.other_participant(request.user),
        'base_template': base_template,
    })


@login_required
def conversation_poll(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.user not in conversation.participants():
        return JsonResponse({'error': 'Access denied'}, status=403)

    last_id = request.GET.get('last_id', '')
    new_messages = conversation.messages.filter(
        id__gt=last_id,
    ).exclude(sender=request.user).order_by('created_at') if last_id else conversation.messages.exclude(sender=request.user).order_by('created_at')

    Message.objects.filter(
        conversation=conversation,
        is_read=False,
    ).exclude(sender=request.user).update(is_read=True)

    Notification.objects.filter(
        user=request.user,
        type=Notification.TypeChoices.MESSAGE_RECEIVED,
        related_conversation=conversation,
        is_read=False,
    ).update(is_read=True)

    data = {
        'messages': [
            {
                'id': str(m.id),
                'content': m.content,
                'sender': m.sender.full_name if m.sender else 'Système',
                'created_at': m.created_at.isoformat(),
                'is_mine': m.sender == request.user,
                'rendered_html': render_to_string('messaging/snippets/message_bubble.html', {
                    'message': m, 'request_user': request.user,
                }),
            }
            for m in new_messages
        ],
    }
    return JsonResponse(data)
