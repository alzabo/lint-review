import logging

log = logging.getLogger(__name__)


class Review(object):
    """
    Holds the comments from a review can
    add track problems logged and post new problems
    to github.
    """

    def __init__(self, gh, number):
        self._gh = gh
        self._comments = {}
        self._number = number

    def comments(self, filename):
        return self._comments.get(filename)

    def publish(self, problems):
        self.load_comments()
        self.remove_existing(problems)
        self.publish_new_problems()

    def load_comments(self):
        """
        Load the existing comments on a pull request

        Results in a structure that is similar to the one used
        for problems
        """
        log.debug("Loading comments for pull request '%s'", self._number)
        comments = self._gh.pull_requests.comments.list(self._number).all()

        for comment in comments:
            filename = comment.path
            if not self._comments.get(filename):
                self._comments[filename] = []
            if not comment.position:
                log.debug("Ignoring outdated diff comment '%s'", comment.id)
                continue
            content = (int(comment.position), comment.body)
            self._comments[filename].append(content)

    def remove_existing(self, problems):
        """
        Modifies the problems parameter removing
        problems that already have matching comments.
        Filters the problems based on existing comments.

        Remove problems that match the line + comment body of
        an existing comment. We'll assume the program put
        the comment there, and not a human.
        """
        for filename, comments in self._comments.iteritems():
            for comment in comments:
                problems.remove(filename, comment[0], comment[1])


class Problems(object):
    """
    Collection class for holding all the problems found
    during automated review.

    Used by tool objects to collect problems, and by
    the Review objects to publish results.
    """

    def __init__(self, base=None):
        self._items = []
        self._base = base

    def _trim_filename(self, filename):
        if not self._base:
            return filename
        return filename[len(self._base):]

    def all(self, filename=None):
        if filename:
            return [error for error in self._items if error[0] == filename]
        return self._items

    def add(self, filename, line, text):
        """
        Add a problem to the review.
        """
        filename = self._trim_filename(filename)
        error = (filename, line, text)
        if error not in self._items:
            self._items.append(error)

    def add_many(self, problems):
        """
        Add multiple problems to the review.
        """
        for p in problems:
            self.add(*p)

    def limit_to(self, changes):
        """
        Limit the contained problems to only those changed
        in the DiffCollection
        """
        self._items = [error for error in self._items
                       if changes.has_line_changed(error[0], error[1])]

    def remove(self, filename, line, comment):
        """
        Remove a problem from the list based on the filename
        line and comment.
        """
        kill = (filename, line, comment)
        self._items = [error for error in self._items
                       if error != kill]

    def __len__(self):
        return len(self._items)