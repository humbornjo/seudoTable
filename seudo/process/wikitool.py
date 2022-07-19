
import wikipedia
import socks
import socket

def wiki_search(men):

    socks.set_default_proxy(socks.SOCKS5,"127.0.0.1",7890)
    socket.socket=socks.socksocket
    titles = wikipedia.search(men, results = 3)

    cands=[]
    for title in titles:
        try:
            page=wikipedia.page(title, auto_suggest=False)
            cands.append({"label":page.title,"url":page.url.replace('s','',1)})
        except wikipedia.DisambiguationError as e:

            ## NOTE: Enable the following codes to query more candidates
            # for opt in e.options:
            #     try:
            #         page = wikipedia.page(opt.replace("\"",""), auto_suggest=False)
            #     except:
            #         continue
            #     urls.append(page.url)
            continue

    return cands

def wiki_suggest(men):

    socks.set_default_proxy(socks.SOCKS5,"127.0.0.1",7890)
    socket.socket=socks.socksocket

    page=None
    try:
        page = wikipedia.page(men, auto_suggest=False)
    except wikipedia.DisambiguationError as e:
        for opt in e.options:
            try:
                page = wikipedia.page(opt, auto_suggest=False)
                break
            except:
                continue
    if page:
        return {"label":page.title,"url":page.url.replace('s','',1)}
    else:
        return None


# page=wikipedia.search("google")
#
# page2=wikipedia.page(r'.google', auto_suggest=False)
