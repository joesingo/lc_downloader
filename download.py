#!/usr/bin/env python3
import os
import sys

from bs4 import BeautifulSoup
import requests


class LCDownloader:
    LC_HOME = "https://learningcentral.cf.ac.uk"
    FILE_URL_PREFIX = "/bbcswebdav"
    FOLDER_URL_PREFIX = "/webapps/"

    def __init__(self, session_id):
        self.session = requests.Session()
        self.session.cookies["s_session_id"] = session_id

    def get_module_urls(self):
        """
        Find all modules and return a generator of (module_name, home_url)
        tuples
        """
        # Note: this is what the JS on LearningCentral does on page load to get
        # the modules list
        modules_url = self.get_abs_url("/webapps/portal/execute/tabs/tabAction")
        resp = BeautifulSoup(self.session.post(modules_url, data={
            "action": "refreshAjaxModule",
            "modId": "_4_1",
            "tabId": "_1_1",
            "tab_tab_group_id": "_1_1",
        }).content, "lxml")

        for link in resp.findAll("a"):
            yield (link.text.strip(), self.get_abs_url(link["href"].strip()))

    def get_learning_materials_url(self, module_home_url):
        """
        Find the 'Learning Materials' link from the home page for a module
        """
        resp = BeautifulSoup(self.session.get(module_home_url).content, "html.parser")
        try:
            lm_link = [l for l in resp.find_all("a") if l.text == "Learning Materials"][0]
        except IndexError:
            print("Could not find Learning Materials link", file=sys.stderr)
            sys.exit(1)
        return self.get_abs_url(lm_link["href"])

    def download_all(self, query, out_dir):
        """
        Find a module whose name matches `query`, and recursively download all
        files under 'Learning Materials', saving them under `out_dir` on the
        file system
        """
        # Find the module the user wants, and get the URL for its 'Learning
        # Materials' page
        lm_url = None
        mod_urls = list(self.get_module_urls())
        for name, home_url in mod_urls:
            if query.lower() in name.lower():
                print("Downloading files for module '{}'".format(name))
                lm_url = self.get_learning_materials_url(home_url)
                break
        else:
            sys.stdout = sys.stderr
            print("Could not find module matching '{}'".format(query))
            print("Modules found were:")
            print("{}".format("\n".join([n for (n, _) in mod_urls])))
            sys.exit(1)

        # Find and download the files
        no_files_found = True
        for path, url in self.find_files(lm_url):
            no_files_found = False
            out_path = os.path.join(out_dir, path)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "wb") as out_file:
                out_file.write(self.session.get(url).content)
            print("Wrote {}".format(out_path))

        if no_files_found:
            print("No files found")

    def get_abs_url(self, rel_path):
        """
        Return an absolute Learning Central URL from a relative one
        """
        return "{}{}".format(self.LC_HOME, rel_path)

    def find_files(self, url, current_path=None):
        """
        Return a generator of tuples (path, url) for all content beneath the
        given URL, recursively searching folders beneath. `path` is directory
        and filename components in the heirearchy.

        `current_path` is a list of path components, i.e. folder names up to
        this point.
        """
        current_path = current_path or []
        resp = BeautifulSoup(self.session.get(url).content, "html.parser")

        for link in resp.select(".contentList a"):
            url_path = link["href"]
            url = self.get_abs_url(url_path)

            # If path part of URL start with this pattern, this is a file and
            # not a folder
            if url_path.startswith(self.FILE_URL_PREFIX):
                # This URL will redirect to another one that contains the
                # filename. Extract this from the 'Location' header
                head = self.session.head(url)
                real_url = self.get_abs_url(head.headers["Location"])
                filename = real_url.split("/")[-1]
                path = os.path.join(*current_path, filename)
                yield (path, real_url)
            # Pattern for folders
            elif url_path.startswith(self.FOLDER_URL_PREFIX):
                yield from self.find_files(url, current_path + [link.text])


if __name__ == "__main__":
    try:
        s_id, module, o_dir = sys.argv[1:4]
    except ValueError:
        print("usage: {} SESSION_ID MODULE_NAME OUTPUT_DIR".format(sys.argv[0]), file=sys.stderr)
        sys.exit(1)

    lc = LCDownloader(s_id)
    lc.download_all(module, o_dir)
