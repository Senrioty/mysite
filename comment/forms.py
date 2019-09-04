from django import forms
from django.contrib.contenttypes.models import ContentType
from django.db.models import ObjectDoesNotExist
from ckeditor.widgets import CKEditorWidget
from comment.models import Comment

class CommentForm(forms.Form):
    content_type = forms.CharField(widget=forms.HiddenInput) #forms.HiddenInput 隐藏不显示，相当于input标签里属性type="hidden"
    object_id = forms.IntegerField(widget=forms.HiddenInput)

    #引入回复后新增的字段，因为需要跳转到富文本编辑器，所以需要通过id把点击的那条评论找到，即父评论id(如果不为0的话)
    reply_comment_id = forms.IntegerField(widget=forms.HiddenInput(attrs={'id':'reply_comment_id'}))


    #text = forms.CharField(widget=forms.Textarea) #设置成textarea标签，而不是input标签
    # 使用ckeditor开源依赖来引入富文本，修改发生为空错误时的信息提示
    text = forms.CharField(widget=CKEditorWidget(config_name='comment_ckeditor'),
                            error_messages={'required': '评论内容不能为空'})

    #初始化会自动调用
    def __init__(self, *args, **kwargs):
        #先处理自己的逻辑
        #优化一：最好不要使用kwargs['user']这种方式，因为用get，即使没有‘user’，那就是取none,不会报错
        #优化二：如果用get,那即使获取到数据，kwargs字典中还有，然后调用super方法时，会看到关键字参数user,那就会判断关键字参数是否合法。
        #       如果没有规定这个参数，而我们写这个参数，会报错，所以用pop获取user关键字参数对应的值时，把user也从kwargs中去掉
        if 'user' in kwargs:
            self.user = kwargs.pop('user')

        super(CommentForm,self).__init__(*args, **kwargs) #调用父类方法


    def clean(self):
        #判断用户是否登录（即使前端有判断，但是我们还是认为前端不可信）
        if self.user.is_authenticated:
            self.cleaned_data['user'] = self.user
        else:
            raise forms.ValidationError('用户尚未登录')

        #评论对象验证，需要两个内容，一个是content_type，另一个是object_id
        content_type = self.cleaned_data['content_type']
        object_id = self.cleaned_data['object_id']
        try:
            model_class = ContentType.objects.get(model=content_type).model_class()
            model_obj = model_class.objects.get(pk=object_id)

            #验证通过后，我们把对象保存到cleaned_data中，供views来做获取
            self.cleaned_data['content_object'] = model_obj

        #因为我们验证就是判断获取的博客对象存不存在，如果不存在，会有ObjectDoesNotExist 异常
        #最好是精确到对应的异常，而不要使用Exception
        except ObjectDoesNotExist as e:
            raise forms.ValidationError('评论对象不存在')

        return self.cleaned_data

    def clean_reply_comment_id(self):
        #判断逻辑如下：
        #单独判断新增的id字段，如果小于0，抛出错误；如果等于0，说明是主评论，因为对博客评论默认是0，那它parent为None;
        #如果不是0且能找到评论，说明是子评论，那parent的值就是这个reply_comment_id对应的评论
        reply_comment_id = self.cleaned_data['reply_comment_id']
        if reply_comment_id < 0:
            raise forms.ValidationError('回复出错')
        elif reply_comment_id == 0:
            self.cleaned_data['parent'] = None #我们新建parent来引入，这样会给view判断提供数据来源
        elif Comment.objects.filter(pk=reply_comment_id).exists():
            self.cleaned_data['parent'] = Comment.objects.get(pk=reply_comment_id)
        else:
            raise forms.ValidationError('回复出错')
        return reply_comment_id