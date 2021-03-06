from data.custom_transforms import *
from data.cvusa_utils import CVUSA
from utils import model_wrapper, parser
from utils.setup_helper import *
from argparse import Namespace
import os
from matplotlib import pyplot

if __name__ == '__main__':
    parse = parser.Parser()
    opt, log_file = parse.parse()
    opt.is_Train = True
    make_deterministic(opt.seed)
    os.environ['CUDA_VISIBLE_DEVICES'] = ','.join(str(x) for x in opt.gpu_ids)

    assert opt.resume != '', "The `--resume` argument has to contain a valid model in the `--results_dir` folder for testing!" 
    
    log = open(log_file, 'a')
    log_print = lambda ms: parse.log(ms, log)

    #define networks
    retrieval = model_wrapper.define_R(ret_method=opt.r_model, polar=opt.polar, gpu_ids=opt.gpu_ids, 
                                sate_size=opt.sate_size, pano_size=opt.pano_size, use_tps=not opt.use_affine)
    print('Init {} as retrieval model'.format(opt.r_model))

    # Initialize network wrapper
    opt.checkpoint = os.path.join(opt.results_dir, opt.resume, 'rgan_best_ckpt.pth')
    model_wrapper = model_wrapper.ModelWrapper(opt, log_file, retrieval)
    # Configure data loader
    val_dataset = CVUSA(root=opt.data_root, csv_file=opt.val_csv, sate_size=opt.sate_size, pano_size=(opt.pano_size[1],opt.pano_size[0]),
                        use_polar=opt.polar, name=opt.name, transform_op=ToTensor())
    val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=opt.batch_size, shuffle=False, num_workers=0)

    log_print('Load test dataset from {}: val_set={}'.format(opt.data_root, len(val_dataset)))
    log_print('length of val loader: {:d}'.format(len(val_loader)))

    model_wrapper.retrieval.eval()
    fake_street_batches_v = []
    street_batches_v = []
    item_ids = []

    for i, data in enumerate(val_loader):
        model_wrapper.set_input(data)
        model_wrapper.eval_model()
        fake_street_batches_v.append(model_wrapper.fake_street_out_val.cpu().data)
        street_batches_v.append(model_wrapper.street_out_val.cpu().data)

    fake_street_vec = torch.cat(fake_street_batches_v, dim=0)
    street_vec = torch.cat(street_batches_v, dim=0)
    dists = 2 - 2 * torch.matmul(fake_street_vec, street_vec.permute(1, 0))

    tp1 = model_wrapper.mutual_topk_acc(dists, topk=1)
    tp5 = model_wrapper.mutual_topk_acc(dists, topk=5)
    tp10 = model_wrapper.mutual_topk_acc(dists, topk=10)

    num = len(dists)
    tp1p = model_wrapper.mutual_topk_acc(dists, topk=0.01 * num)
    acc = Namespace(num=len(dists), tp1=tp1, tp5=tp5, tp10=tp10, tp1p=tp1p)

    log_print('\nEvaluate Samples:{num:d}\nRecall(p2s/s2p) tp1:{tp1[0]:.2f}/{tp1[1]:.2f} ' \
            'tp5:{tp5[0]:.2f}/{tp5[1]:.2f} tp10:{tp10[0]:.2f}/{tp10[1]:.2f} ' \
            'tp1%:{tp1p[0]:.2f}/{tp1p[1]:.2f}'.format(1, num=acc.num, tp1=acc.tp1,
                                                    tp5=acc.tp5, tp10=acc.tp10, tp1p=acc.tp1p))