from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.utils.translation import gettext_lazy as _
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

    conversations = conversations.select_related('application__task').order_by('-last_activity_at')

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

    if conversation.is_closed:
        messages.error(request, _('Cette conversation est clôturée. Vous ne pouvez plus envoyer de messages.'))
        return render(request, 'messaging/conversation_detail.html', {
            'conversation': conversation,
            'chat_messages': message_list,
            'form': None,
            'other_user': conversation.other_participant(request.user),
            'base_template': base_template,
        })

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
            conversation.save(update_fields=['last_activity_at'])

            recipient = conversation.other_participant(request.user)
            Notification.objects.create(
                user=recipient,
                type=Notification.TypeChoices.MESSAGE_RECEIVED,
                title=_('Nouveau message'),
                message=_('Vous avez reçu un nouveau message de la part de %(sender)s au sujet de « %(task)s »') % {
                    'sender': request.user.full_name,
                    'task': conversation.task.title,
                },
                related_conversation=conversation,
            )

            if request.htmx:
                return render(request, 'messaging/snippets/message_bubble.html', {
                    'message': message, 'request_user': request.user,
                })

            return redirect('messaging:conversation_detail', conversation_id=conversation.id)
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
                'sender': m.sender.full_name,
                'created_at': m.created_at.isoformat(),
                'is_mine': m.sender == request.user,
            }
            for m in new_messages
        ],
        'is_closed': conversation.is_closed,
    }
    return JsonResponse(data)
