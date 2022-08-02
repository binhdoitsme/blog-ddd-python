import textwrap

from domain.blog import Blog, BlogProperties


def main():
    blog = Blog(
        title="My new Blog",
        content=textwrap.dedent("""This is the original content"""),
    )
    blog.update(
        BlogProperties(
            title="My new Blog (edited)", content="This is the new content"
        )
    )
    props: BlogProperties = BlogProperties(
        title="My new Blog (edited)",
        content="This is the new content",
        item="asdasd",
    )
    blog.update(props)
    print(blog)


if __name__ == "__main__":
    main()
