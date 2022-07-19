import numpy as np
import transformers
import torch
from transformers import BertTokenizer, BertModel, BertForMaskedLM

# words="Populated Place"
#
# bert_tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
# words = bert_tokenizer.tokenize(words)
# indexed_tokens = bert_tokenizer.convert_tokens_to_ids(words)
#
# segments_ids = [1] * len(words)
#
# tokens_tensor = torch.tensor([indexed_tokens])
# segments_tensors = torch.tensor([segments_ids])
#
# # Load pre-trained model (weights)
# model = BertModel.from_pretrained('bert-base-uncased',
#                                   output_hidden_states = True, # Whether the model returns all hidden-states.
#                                   )
#
# # Put the model in "evaluation" mode, meaning feed-forward operation.
# model.eval()
#
# hidden_states = model(tokens_tensor, segments_tensors)[2]
#
# token_vecs = hidden_states[-2][0]
#
# semantic_embed = torch.mean(token_vecs, dim=0)
#
# print(semantic_embed.size())

### 768+layerNum+Confidence==770
### 10*770 stack ---> 770*1 == 10*1
### backp




import torch
from tqdm.auto import tqdm
import torch.nn as nn
from torch.optim import AdamW
from torch.utils.data import TensorDataset,DataLoader,random_split

class ResNet(torch.nn.Module):
    def __init__(self, module):
        super().__init__()
        self.module = module

    def forward(self, inputs):
        return self.module(inputs) + inputs

# Create the BertClassfier class
class HiercolClassifier(nn.Module):
    """Bert Model for Classification Tasks.
    """

    def __init__(self, freeze_bert=False):
        super(HiercolClassifier, self).__init__()
        D_in, H, D_out = 770, 770, 1
        if torch.cuda.is_available():
            self.device=torch.device("cuda")
        else:
            self.device=torch.device("cpu")

        self.classifier = nn.Sequential(
            nn.Linear(D_in, H),
            ResNet(
                torch.nn.Sequential(
                    nn.Linear(H, 1024),
                    nn.Dropout(0.6),
                    nn.Linear(1024, H),
                    nn.ReLU(),
                )
            ),
            nn.Linear(H, D_out),
            nn.Sigmoid()
        )


        # Freeze the BERT model
        if freeze_bert:
            for param in self.bert.parameters():
                param.requires_grad = False

    def process_data(self, train_data, test_data, batch_size):
        self.train_data=TensorDataset(train_data[0],train_data[1])
        self.test_data = test_data
        self.test_len,self.train_len=len(test_data[0]),len(train_data[0])
        self.train_loader = DataLoader(self.train_data,batch_size=batch_size,shuffle=True)

    def forward(self, input, *args, **kwargs):
        # Feed input to BERT
        # outputs = self.bert(input_ids=input_ids,
        #                     attention_mask=attention_mask, *args, **kwargs)
        # # print(outputs.shape)
        # # Extract the last hidden state of the token `[CLS]` for classification task
        # last_hidden_state_cls = outputs[0][:, 0, :]

        # Feed input to classifier to compute logits
        logits = self.classifier(input)

        return logits

    def train_model(self,epochs=500,batch_size=64,lr=4e-5):
        model=self.classifier.to(self.device)
        optimizer = AdamW(model.parameters(), lr=lr)
        criterion=nn.MSELoss()
        best_loss,best_acc,best_epoch=np.inf,0,0
        global_step=0

        train_loader = self.train_loader

        for epoch in range(epochs):
            model.train()
            loop=tqdm(enumerate(train_loader),total=len(train_loader))

            loss_sum=0
            acc_num=0
            for step,(x,y) in loop:
                x,y =x.to(self.device),y.to(self.device)

                ## apply model
                logits=model(x)
                loss=criterion(logits,y)

                ## backprop
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                global_step+=1

                ## do log work
                if loss<=best_loss:
                    best_loss=loss

                loss_sum+=loss
                squeezed_logits=torch.squeeze(logits,dim=-1)
                squeezed_y=torch.squeeze(y,dim=-1)
                arg=torch.argmax(squeezed_logits,dim=-1)
                row_selector=[i for i in range(len(y))]
                selected=squeezed_y[row_selector, list(arg)]
                acc_num+=torch.sum(selected)
                loop.set_description(f'Epoch[{epoch + 1}/{epochs}]')
                loop.set_postfix(loss=loss_sum, acc=acc_num / self.train_len)

            total=len(self.test_data[0])
            recall=0
            prec=0
            for i in range(total):
                xx, yy = self.test_data[0][i].to(self.device), self.test_data[1][i].to(self.device)

                if torch.sum(yy)==0:
                    recall+=1
                    continue
                else:

                    gt=torch.argmax(yy,dim=0)
                    model.eval()
                    logits = model(xx)
                    ans=torch.argmax(logits,dim=0)
                    prec+=(ans==gt)
            print("test_acc is %.4f" % (prec/(total-recall)))



# if __name__=="__main__":
#     # fake_embed=torch.rand(500,8,768).to(torch.float32)
#     # fake_laynum=torch.tensor(np.random.randint(3,size=(500,8,1))).to(torch.float32)
#     # fake_conf=torch.tensor(np.random.normal(size=(500,8,1))).to(torch.float32)
#     # train_x=torch.concat([fake_embed,fake_laynum,fake_conf],dim=2)
#     # train_y=torch.tensor(np.random.randint(2,size=(500,8,1))).to(torch.float32)
#     train_x=torch.load("./dataset_x.pt")
#     print(train_x.size)
#     train_y=torch.load("./dataset_y.pt")
#
#     l=len(train_x)
#     train_set_size = int(len(train_x) * 0.8)
#     test_set_size = len(train_x) - train_set_size
#
#     train_data=[train_x[:train_set_size],train_y[:train_set_size]]
#     test_data=[train_x[train_set_size:],train_y[train_set_size:]]
#
#     hcol=HiercolClassifier()
#     hcol.process_data(train_data,test_data,4)
#     hcol.train(100,3e-5)
#     torch.save(hcol, "100_hcol.pth")