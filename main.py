from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import SlideTransition
from telas import *
from botoes import *
import requests
from bannervenda import BannerVenda
import os
from functools import partial
from myfirebase import MyFirebase
from bannervendedor import BannerVendedor
from datetime import date

GUI = Builder.load_file("main.kv")
class MainApp(App):
    cliente = None
    produto = None
    unidade = None


    # Função responsável pela construção da interface
    def build(self):
        self.firebase = MyFirebase()
        return GUI

    # Função é executada assim quando o app é iniciado
    def on_start(self):
        # Carregar as fotos de perfil
        arquivos = os.listdir("icones/fotos_perfil")
        pagina_foto_perfil = self.root.ids["fotoperfilpage"]
        lista_fotos = pagina_foto_perfil.ids["lista_fotos_perfil"]

        for foto in arquivos:
            # Partial é usado para passar um parâmetro para a função mudar_foto_perfil, que já é parâmetro de ImageButton
            imagem = ImageButton(source=f"icones/fotos_perfil/{foto}", on_release=partial(self.mudar_foto_perfil, foto))
            lista_fotos.add_widget(imagem)

        # Carregar as fotos dos clientes
        arquivos = os.listdir("icones/fotos_clientes")
        pagina_adicionarclientes = self.root.ids["adicionarvendaspage"]
        lista_clientes = pagina_adicionarclientes.ids["lista_clientes"]

        for foto_cliente in arquivos:
            imagem = ImageButton(source=f"icones/fotos_clientes/{foto_cliente}",
                                 on_release=partial(self.selecionar_cliente, foto_cliente))
            label = LabelButton(text=foto_cliente.replace(".png","").capitalize(),
                                on_release=partial(self.selecionar_cliente, foto_cliente))
            lista_clientes.add_widget(imagem)
            lista_clientes.add_widget(label)

        # Carregar as fotos dos produtos
        arquivos = os.listdir("icones/fotos_produtos")
        pagina_adicionarprodutos = self.root.ids["adicionarvendaspage"]
        lista_produtos = pagina_adicionarprodutos.ids["lista_produtos"]

        for foto_produto in arquivos:
            imagem = ImageButton(source=f"icones/fotos_produtos/{foto_produto}",
                                 on_release = partial(self.selecionar_produto, foto_produto))
            label = LabelButton(text=foto_produto.replace(".png","").capitalize(),
                                on_release = partial(self.selecionar_produto, foto_produto))
            lista_produtos.add_widget(imagem)
            lista_produtos.add_widget(label)

        # Carregar a data
        pagina_adicionarprodutos = self.root.ids["adicionarvendaspage"]
        label_data = pagina_adicionarprodutos.ids["id_label_data"]
        label_data.text = f"Data: {date.today().strftime('%d/%m/%Y')}"
        # Carregar as informações do usuário
        self.carregar_infos_usuario()


    def carregar_infos_usuario(self):
        try:
            # Mantendo o usuário logado através do refresh_token
            with open("refreshtoken.txt", "r") as arquivo:
                refresh_token = arquivo.read()

            local_id, id_token = self.firebase.trocar_token(refresh_token)
            self.local_id = local_id
            self.id_token = id_token


            # Pegando informações do BD
            requisicao = requests.get(f"https://appvendashash-9c9fb-default-rtdb.firebaseio.com/{self.local_id}.json?auth={self.id_token}")
            requisicao_dic = requisicao.json()

            # Mudando a foto de perfil
            avatar = requisicao_dic["avatar"]
            self.avatar = avatar
            foto_perfil = self.root.ids["foto_perfil"]
            foto_perfil.source = f"icones/fotos_perfil/{avatar}"

            # Preencher ID único
            id_vendedor = requisicao_dic["id_vendedor"]
            self.id_vendedor = id_vendedor
            pagina_ajustes = self.root.ids["ajustespage"]
            pagina_ajustes.ids["id_vendedor"].text = f"Seu ID único {id_vendedor}"

            # Preencher total de vendas
            total_vendas = requisicao_dic["total_vendas"]
            self.total_vendas = total_vendas
            homepage = self.root.ids["homepage"]
            homepage.ids["id_label_total_vendas"].text = f"[color=#000000]Total de vendas: [/color][b]R$ {total_vendas}[/b]"

            # Preencher equipe
            self.equipe = requisicao_dic["equipe"]

            # Lista de vendas
            try:
                pagina_hoomepage = self.root.ids["homepage"]
                lista_vendas = pagina_hoomepage.ids["lista_vendas"]
                vendas = requisicao_dic["vendas"]
                self.vendas = vendas
                for id_venda in vendas:
                    venda = vendas[id_venda]
                    banner = BannerVenda(cliente=venda["cliente"], foto_cliente=venda["foto_cliente"],
                                         produto=venda["produto"], foto_produto=venda["foto_produto"],
                                         data=venda["data"], preco=venda["preco"],
                                         unidade=venda["unidade"], quantidade=venda["quantidade"])


                    lista_vendas.add_widget(banner)
                # Caso o vendedor ainda não tenha nenhuma venda
            except:
                pass

            equipe = requisicao_dic["equipe"]
            lista_equipe = equipe.split(",")

            pagina_listavendedor = self.root.ids["listarvendedorespage"]
            lista_vendedores = pagina_listavendedor.ids["lista_vendedores"]

            for id_outro_vendedor_equipe in lista_equipe:
                if id_outro_vendedor_equipe != "":
                    banner_vendedor = BannerVendedor(id_vendedor=id_outro_vendedor_equipe)
                    lista_vendedores.add_widget(banner_vendedor)

            # Para quando o usuaário entrar no app já estando logado
            self.mudar_tela("homepage", "left")
        except:
            pass


    def mudar_tela(self, id_tela, direcao_transicao):
        gerenciador_telas = self.root.ids["screen_manager"]
        gerenciador_telas.transition = SlideTransition(direction=direcao_transicao)
        gerenciador_telas.current = id_tela

    def mudar_foto_perfil(self, foto, *args):
        # Muda a foto temporariamente enquanto o aplicativo está aberto
        foto_perfil = self.root.ids["foto_perfil"]
        foto_perfil.source = f"icones/fotos_perfil/{foto}"

        # Para fazer um patch no firebase, a data deve ser um dicionário formatado em texto, sendo que todos os itens devem
        # estar dentro de aspas duplas
        info = f'{{"avatar": "{foto}" }}'
        requisicao = requests.patch(f"https://appvendashash-9c9fb-default-rtdb.firebaseio.com/{self.local_id}.json?auth={self.id_token}",
                                    data=info)


    def adicionar_vendedor(self, id_vendedor_adicionado):
        link = f'https://appvendashash-9c9fb-default-rtdb.firebaseio.com/.json?orderBy="id_vendedor"&equalTo="{id_vendedor_adicionado}"'
        requisicao = requests.get(link)
        requisicao_dic = requisicao.json()

        pagina_adicionar_vendedor = self.root.ids['adicionarvendedorpage']
        mensagem_texto = pagina_adicionar_vendedor.ids['mensagem_outro_vendedor']

        if requisicao_dic == {}:
            mensagem_texto.text = "Vendedor não encontrado"
        else:
            equipe = self.equipe.split(",")
            if id_vendedor_adicionado in equipe:
                mensagem_texto.text = "Vendedor já faz parte da equipe"
            else:
                self.equipe = self.equipe + f",{id_vendedor_adicionado}"
                info =f'{{"equipe":"{self.equipe}"}}'
                requests.patch(f"https://appvendashash-9c9fb-default-rtdb.firebaseio.com/{self.local_id}.json?auth={self.id_token}",
                               data=info)
                mensagem_texto.text = "Vendedor adicionado com sucesso"
                # Já adiciona este novo vendedor à página de acompanhar os vendedores
                pagina_listavendedor = self.root.ids["listarvendedorespage"]
                lista_vendedores = pagina_listavendedor.ids["lista_vendedores"]
                banner_vendedor = BannerVendedor(id_vendedor=id_vendedor_adicionado)
                lista_vendedores.add_widget(banner_vendedor)

    def selecionar_cliente(self, foto, *args):
        pagina_adicionarclientes = self.root.ids["adicionarvendaspage"]
        lista_clientes = pagina_adicionarclientes.ids["lista_clientes"]

        self.cliente = foto.replace(".png", "")

        # Pintar todas os textos de branco
        for item in list(lista_clientes.children):
            item.color = (1,1,1,1)
            try:
                texto = item.text
                texto = texto.lower() + '.png'
                if foto == texto:
                    item.color = (0, 207/255, 219/255, 1)
            except:
                pass


    def selecionar_produto(self, foto, *args):
        pagina_adicionarvendas = self.root.ids["adicionarvendaspage"]
        lista_produtos = pagina_adicionarvendas.ids["lista_produtos"]

        self.produto = foto.replace(".png","")

        # Pintar todas os textos de branco
        for item in list(lista_produtos.children):
            item.color = (1, 1, 1, 1)
            try:
                texto = item.text
                texto = texto.lower() + '.png'
                if foto == texto:
                    item.color = (0, 207 / 255, 219 / 255, 1)
            except:
                pass

    def selecionar_unidade(self, id_label, *args):
        pagina_adicionarvendas = self.root.ids["adicionarvendaspage"]
        self.unidade =id_label.replace("unidades_","")
        pagina_adicionarvendas.ids["unidades_kg"].color = (1,1,1,1)
        pagina_adicionarvendas.ids["unidades_unidades"].color = (1,1,1,1)
        pagina_adicionarvendas.ids["unidades_litro"].color = (1,1,1,1)

        pagina_adicionarvendas.ids[id_label].color = (0, 207 / 255, 219 / 255, 1)

    def adicionar_venda(self):
        cliente = self.cliente
        produto = self.produto
        unidade = self.unidade

        pagina_adicionarvendas = self.root.ids["adicionarvendaspage"]
        data = pagina_adicionarvendas.ids["id_label_data"].text.replace("Data: ", "")
        preco = pagina_adicionarvendas.ids["preco_total"].text
        quantidade = pagina_adicionarvendas.ids["quantidade_total"].text


        # Verificando se o usário preencheu todos os campos para cadastrar a venda e sinalizando um campo não preenchido
        if not cliente:
            pagina_adicionarvendas.ids["label_selecione_cliente"].color = (1,0,0,1)
        else:
            pagina_adicionarvendas.ids["label_selecione_cliente"].color = (1,1,1,1)

        if not produto:
            pagina_adicionarvendas.ids["label_selecione_produto"].color = (1,0,0,1)
        else:
            pagina_adicionarvendas.ids["label_selecione_produto"].color = (1,1,1,1)

        if not unidade:
            pagina_adicionarvendas.ids["unidades_kg"].color = (1,0,0,1)
            pagina_adicionarvendas.ids["unidades_unidades"].color = (1,0,0,1)
            pagina_adicionarvendas.ids["unidades_litro"].color = (1,0,0,1)

        if not preco:
            pagina_adicionarvendas.ids["label_preco_total"].color = (1, 0, 0, 1)
        else:
            try:
                preco = float(preco)
            except:
                pagina_adicionarvendas.ids["label_preco_total"].color = (1, 0, 0, 1)

        if not quantidade:
            pagina_adicionarvendas.ids["label_quantidade"].color = (1, 0, 0, 1)
        else:
            try:
                quantidade = float(quantidade)
            except:
                pagina_adicionarvendas.ids["label_quantidade"].color = (1, 0, 0, 1)


        # Caso o usuário tenha preenchido tudo - efetivamente adiconar a venda no banco de dados e na homepage
        if cliente and produto and unidade and quantidade and type(preco) == float and type(quantidade) == float:
            foto_produto = produto + ".png"
            foto_cliente = cliente + ".png"

            # Cadastrando a venda no banco de dados
            info = f'{{"cliente": "{cliente}", "produto": "{produto}", "foto_cliente": "{foto_cliente}", "foto_produto": "{foto_produto}", "data": "{data}", "unidade": "{unidade}", "preco": "{preco}", "quantidade": "{quantidade}"}}'
            requests.post(f"https://appvendashash-9c9fb-default-rtdb.firebaseio.com/{self.local_id}/vendas.json?auth={self.id_token}",data=info)

            banner = BannerVenda(cliente=cliente, produto=produto, foto_cliente=foto_cliente, foto_produto=foto_produto,
                                 data=data, preco=preco, quantidade=quantidade, unidade=unidade)
            pagina_hoomepage = self.root.ids["homepage"]
            lista_vendas = pagina_hoomepage.ids["lista_vendas"]
            lista_vendas.add_widget(banner)


            # Atualizando o total vendas do usuário no banco e aqui no app
            requisicao = requests.get(f"https://appvendashash-9c9fb-default-rtdb.firebaseio.com/{self.local_id}/total_vendas.json?auth={self.id_token}")
            total_vendas = float(requisicao.json())
            total_vendas += preco

            info = f'{{"total_vendas": "{total_vendas}"}}'
            requests.patch(f"https://appvendashash-9c9fb-default-rtdb.firebaseio.com/{self.local_id}.json?auth={self.id_token}", data=info)

            homepage = self.root.ids["homepage"]
            homepage.ids["id_label_total_vendas"].text = f"[color=#000000]Total de vendas: [/color][b]R$ {total_vendas}[/b]"

            self.mudar_tela("homepage", "left")

        cliente = None
        produto = None
        unidade = None


    def carregar_todas_vendas(self):
        pagina_todasvendas = self.root.ids["todasvendaspage"]
        lista_vendas = pagina_todasvendas.ids["lista_vendas"]

        # Evitando carregar múltiplas vezes as mesmas vendas
        for item in list(lista_vendas.children):
            lista_vendas.remove_widget(item)

        # Pegando informações da empresa
        requisicao = requests.get(f'https://appvendashash-9c9fb-default-rtdb.firebaseio.com/.json?orderBy="id_vendedor"')
        requisicao_dic = requisicao.json()

        # Mudando a foto de perfil da empresa
        foto_perfil = self.root.ids["foto_perfil"]
        foto_perfil.source = f"icones/fotos_perfil/hash.png"

        total_vendas = 0


        # Percorrendo todos os usuários
        for local_id_usuario in requisicao_dic:
            # Pegando, caso haja, as vendas do usuário
            try:
                vendas = requisicao_dic[local_id_usuario]["vendas"]
                # Percorrendo cada venda do usuário e criando um banner para ela
                for id_venda in vendas:
                    venda = vendas[id_venda]
                    total_vendas += float(venda["preco"])
                    banner = BannerVenda(cliente=venda["cliente"], produto=venda["produto"], foto_cliente=venda["foto_cliente"],
                                         foto_produto=venda["foto_produto"],
                                         data=venda["data"], preco=venda["preco"], quantidade=venda["quantidade"], unidade=venda["unidade"])
                    lista_vendas.add_widget(banner)
            except:
                pass


        # Preencher total de vendas
        homepage = self.root.ids["todasvendaspage"]
        homepage.ids["id_label_total_vendas"].text = f"[color=#000000]Total de vendas: [/color][b]R$ {total_vendas}[/b]"

        self.mudar_tela("todasvendaspage", "left")



    def sair_todas_vendas(self, id_tela, direcao_transicao):
        foto_perfil = self.root.ids["foto_perfil"]
        foto_perfil.source = f"icones/fotos_perfil/{self.avatar}"
        self.mudar_tela(id_tela, direcao_transicao)

    def carregar_vendas_vendedor(self, dic_info_vendedor, *args):


        # Pegando, caso haja, as vendas do usuário
        try:
            pagina_vendasoutrovendedor = self.root.ids["vendasoutrovendedorpage"]
            lista_vendas = pagina_vendasoutrovendedor.ids["lista_vendas"]

            # Resolve o problema das vendas sobrepostas
            for item in list(lista_vendas.children):
                lista_vendas.remove_widget(item)

            vendas = dic_info_vendedor["vendas"]
            # Percorrendo cada venda do usuário e criando um banner para ela
            for id_venda in vendas:
                venda = vendas[id_venda]
                banner = BannerVenda(cliente=venda["cliente"], produto=venda["produto"],
                                     foto_cliente=venda["foto_cliente"],
                                     foto_produto=venda["foto_produto"],
                                     data=venda["data"], preco=venda["preco"], quantidade=venda["quantidade"],
                                     unidade=venda["unidade"])
                lista_vendas.add_widget(banner)
        except:
            pass

        # Preencher total de vendas
        total_vendas = dic_info_vendedor["total_vendas"]
        pagina_vendasoutrovendedor.ids["id_label_total_vendas"].text = f"[color=#000000]Total de vendas: [/color][b]R$ {total_vendas}[/b]"

        # Mudando a foto de perfil da empresa
        foto_perfil = self.root.ids["foto_perfil"]
        foto_perfil.source = f"icones/fotos_perfil/{dic_info_vendedor['avatar']}"

        self.mudar_tela("vendasoutrovendedorpage", "left")
MainApp().run()