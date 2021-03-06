import argparse
import os
import torch
import time

def image_size(s):
    try:
        x, y = map(int, s.split(','))
        return x, y
    except:
        raise argparse.ArgumentTypeError("Image size must be x,y")


class Parser():
    """ Helper class for parsing arguments and logging."""
    def __init__(self):
        self.initialized = False

    def initialize(self, parser):
        #basic parameters
        parser.add_argument('--results_dir', '-o', type=str, default='./output', help='models are saved here')
        parser.add_argument('--name', type=str, default='', help=' ')
        parser.add_argument('--seed', type=int, default=10)
        parser.add_argument('--phase', type=str, default='train', help='')
        parser.add_argument('--gpu_ids', type=str, default='0', help='gpu ids: e.g. 0  0,1')

        parser.add_argument('--isTrain', default=True, action='store_true')
        parser.add_argument('--resume', type=str, default='', help='model to load from `--results_dir`')
        parser.add_argument('--start_epoch', type=int, default=0)

        #data parameters
        parser.add_argument('--data_root', type=str, default= './data/CVUSA') # './data/VIGOR'
        parser.add_argument('--train_csv', type=str, default='train-19zl.csv')
        parser.add_argument('--val_csv', type=str, default='val-19zl.csv')
        parser.add_argument('--sate_size', help="Size of the satellite images (HxW) to be fed \
            into the model", default="256, 256", type=image_size, nargs=2) # default for vigor: (160, 160)
        parser.add_argument('--pano_size', help="Size of the panorama images (HxW) to be fed \
            into the model", default="112, 616", type=image_size, nargs=2) # default for vigor: (160, 320)

        #vigor parameters 
        parser.add_argument('--vigor_mode', type=str, default= 'train_SAFA_CVM-loss-same') # dataloader will use substrings of it
        parser.add_argument('--vigor_dim', type=str, default=4096)

        #model parameters
        parser.add_argument('--r_model', type=str, default='SAFA')
        parser.add_argument('--model_name', type=str, default='tps')
        parser.add_argument('--checkpoint', type=str, default=None)
        parser.add_argument('--polar', default=False, action='store_true', help='True -> polar transf; False -> spatial transf')
        parser.add_argument('--use_affine', default=False, action='store_true', help='Has effect only if --polar is not specified. \
            True -> spatial transformer uses affine transformation; False -> spatial transformer uses thin plate spline transformation')

        #train parameters
        parser.add_argument("--n_epochs", type=int, default=20, help="number of epochs of combined training")
        parser.add_argument("--batch_size", type=int, default=32, help="size of the batches")
        parser.add_argument("--lr_r", type=float, default=0.0001, help="adam: learning rate")
        parser.add_argument("--b1", type=float, default=0.5, help="adam: decay of first order momentum of gradient")
        parser.add_argument("--b2", type=float, default=0.999, help="adam: decay of first order momentum of gradient")

        #loss parameters
        parser.add_argument("--lambda_l1", type=int, default=1, help="loss weight for l1")
        parser.add_argument("--lambda_ret1", type=int, default=1, help="loss weight for retrieval")
        parser.add_argument("--lambda_sm", type=int, default=10, help="loss weight for soft margin")
        parser.add_argument("--hard_topk_ratio", type=float, default=1.0, help="hard negative ratio")
        parser.add_argument("--hard_decay1_topk_ratio", type=float, default=0.1, help="hard negative ratio")
        parser.add_argument("--hard_decay2_topk_ratio", type=float, default=0.05, help="hard negative ratio")
        parser.add_argument("--hard_decay3_topk_ratio", type=float, default=0.01, help="hard negative ratio")

        self.initialized = True
        return parser

    def gather_options(self):
        if not self.initialized:
            parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
            parser = self.initialize(parser)

        # get the basic options
        opt, _ = parser.parse_known_args() # add `args=[]` as argument when using jupyter
        # save and return the parser
        self.parser = parser
        print("----------------- \n", opt)
        
        return parser.parse_args()


    def print_options(self, opt):

        message = ''
        message += '----------------- Options ---------------\n'
        for k, v in sorted(vars(opt).items()):
            comment = ''
            default = self.parser.get_default(k)
            if v != default:
                comment = '\t[default: %s]' % str(default)
            message += '{:>25}: {:<30}{}\n'.format(str(k), str(v), comment)
        message += '----------------- End -------------------'
        print(message)

        # save to the disk
        if opt.resume == '':
            prefix = '{}_lrr{}_batch{}_{}'.format(opt.model_name, opt.lr_r, opt.batch_size,
                                                                time.strftime("%Y%m%d-%H%M%S"))
            out_dir = os.path.join(opt.results_dir, prefix)
            os.makedirs(out_dir)
        else:
            out_dir = os.path.join(opt.results_dir, opt.resume)
            if not os.path.exists(out_dir):
                raise NotADirectoryError("The `--resume` argument is not a valid model in the `--results_dir` folder!")

        file_name = os.path.join(out_dir, 'log.txt')
        with open(file_name, 'at') as opt_file:
            opt_file.write(message)
            opt_file.write('\n')
            opt_file.flush()
        return file_name


    def parse(self):
        opt = self.gather_options()
        file = self.print_options(opt)
        str_ids = opt.gpu_ids.split(',')
        opt.gpu_ids = []
        for str_id in str_ids:
            id = int(str_id)
            if id >= 0:
                opt.gpu_ids.append(id)
        if len(opt.gpu_ids) > 0:
            torch.cuda.set_device(opt.gpu_ids[0])

        self.opt = opt
        return self.opt, file

    def log(self, ms, log=None):
        print(ms)
        if log:
            log.write(ms + '\n')
            log.flush()