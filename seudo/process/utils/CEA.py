import nltk
import numpy as np
import Levenshtein

def intersection(main_sent, sub_sent):
    stop_words = set(nltk.corpus.stopwords.words('english'))
    stop_words.update(['.', ',', '"', "'", '?', '!', ':', ';', '(', ')', '[', ']', '{', '}', None])
    mains = [i for i in nltk.word_tokenize(main_sent.lower()) if i not in stop_words]
    subs = [i for i in nltk.word_tokenize(sub_sent.lower()) if i not in stop_words]

    res_list = []

    for token in subs:
        sim = 0
        for text in mains:
            edist = Levenshtein.ratio(token, text)
            if edist > sim:
                sim = edist
        res_list.append(sim)
    error = len(subs) // 5
    while error > 0:
        res_list.pop(int(np.argmin(res_list)))
        error -= 1

    return np.mean(res_list)


def statistic_type(self, dict, list):
    for ent in list:
        try:
            dict[-1] += 1
        except:
            dict[-1] = 1

        for type in self._sparql.get_type(ent):
            try:
                dict[type] += 1
            except:
                dict[type] = 1

    return dict

def get_bs(abst, ent_list):
    # abst = self._sparql.get_abstract(ent)
    # prop = self._sparql.get_property(ent)
    # prop = ','.join([p[1] for p in prop])

    # ent_list = [self._table[row][c] for c in self._target['col']]
    sim_abst = intersection(abst, ', '.join(ent_list))
    # sim_prop = intersection(prop, ', '.join(ent_list))
    return sim_abst


def bs_cell_confidence(datas,cells,dictionary,row_num,cols):
    cells_type=None
    for row in range(row_num):
        for col in cols:
            a=cells[str(row)]
            if cells[str(row)][str(col)]:
                if isinstance(cells[str(row)][str(col)],list):
                    cells_type='seudo'
                    break

    ## num(wiki2db) == 0

    if cells_type=='seudo':
        return bs_seudo_confidence(datas,cells,dictionary,row_num,cols)
    else:
        return bs_direct_confidence(datas,cells,dictionary,row_num,cols)

def bs_direct_confidence(datas,cells,dictionary,row_num,cols):

    for row in range(row_num):
        for col in cols:
            cell=cells[str(row)][str(col)]
            if cell:
                if cell["bs"] == -1:
                    cand=cell["url"]
                    abst=dictionary["abstract"][cand]
                    label=dictionary["label"][cand]
                    context=[]
                    for ccol in cols:
                        context.append(datas[row][ccol])
                    bs=get_bs(label,datas[row][col])
                    if label == datas[row][col]:
                        bs = 5
                    if abst:
                        bs+=get_bs(abst,context)

                    cell["bs"]=bs
    return cells

def bs_seudo_confidence(datas,cells,dictionary,row_num,cols):

    for row in range(row_num):
        for col in cols:
            cell_list=cells[str(row)][str(col)]
            if cell_list:
                context = []
                for ccol in cols:
                    context.append(datas[row][ccol])

                for cand in cell_list:
                    if cand["bs"] == -1:
                        url = cand["url"]
                        abst = dictionary["abstract"][url]
                        label = dictionary["label"][url]
                        bs = get_bs(label, datas[row][col])
                        factor=1
                        if label==datas[row][col]:
                            bs = 5
                        if cand["fix"]==1:
                            bs=1
                            factor = 2

                        if cand["fix"]==-1:
                            bs=0.5

                        if abst:
                            bs += get_bs(abst, context)*factor

                        cand["bs"] = bs

    return cells

