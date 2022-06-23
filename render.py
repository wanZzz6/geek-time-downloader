import datetime


class Render(object):
    def render(self, info) -> str:
        raise NotImplementedError()


class MarkdownRender(Render):
    def __init__(self, article_info):
        pass

    def render(self, info) -> str:
        # TODO
        pass


class CommentHtmlRender(Render):

    def __init__(self):
        with open(r'./comment.css') as f:
            self.css_content = f.read()

    def _render_sub_comment(self, replies, level: int = 0) -> str:
        if not replies:
            return ''
        base_str = '{}'
        if level == 0:
            base_str = """
                    <div data-commentnest="commentNestWrap" data-index="0" class="CommentNestPC_commentWrap_2yuwI">
                        <div class="CommentNestPC_commentList_2iyZS">
                        {}
                        </div>
                    </div>
                        """
        sub_comment_list = []
        for comment in replies:
            sub_comment_list.append(f"""
                            <div class="{'CommentNestPC_rootItem_1Z-FB' if level == 0 else 'CommentNestPC_commentChildWrap_1l4eG'}">
                                <div class="CommentNestPC_info_1hY1F">
                                    <div class="UserName_userInfo_-zvn6">
                                        <span>{comment['user_name']}</span>
                                    </div>
                                    <div class="CommentNestPC_bd_2qXmR">{comment['comment_content']}</div>
                                    <div class="CommentNestPC_control_2ziRW">
                                        <div class="CommentNestPC_time_2JZ0H">{datetime.datetime.fromtimestamp(comment['comment_ctime'])}</div>
                                    </div>
                                </div>
                                {self._render_sub_comment(comment.get('replies'), level + 1)}
                            </div>
        """)
        return base_str.format(''.join(sub_comment_list))

    def render(self, comments) -> str:

        comment_lis = []
        for comment in comments:
            comment_lis.append(f"""
        <li>
            <div class="CommentItemPC_main_2sjJG">
                <div class="author-time">{comment['user_name']}</div>
                <div class="CommentItemPC_info_36Chp">
                    <div class="CommentItemPC_bd_2_Qra">{comment['comment_content']}</div>
                    <div class="CommentNestPC_control_2ziRW">
                        <div class="CommentNestPC_time_2JZ0H">{datetime.datetime.fromtimestamp(comment['comment_ctime'])}</div>
                    </div>
                    {self._render_sub_comment(comment.get('replies'), 0)}
                </div>
            </div>
        </li>""")

        return r'<br><br><br><style type="text/css">{}</style><ul>{}</ul>'.format(self.css_content,
                                                                                  ''.join(comment_lis))
