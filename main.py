from StyleGAN2 import StyleGAN2
import argparse
from utils import *

def parse_args():
    desc = "Tensorflow implementation of StyleGAN2"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('--phase', type=str, default='train', help='[train, test, draw]')
    parser.add_argument('--draw', type=str, default='uncurated', help='[uncurated, style_mix, truncation_trick]')

    parser.add_argument('--dataset', type=str, default='FFHQ', help='dataset_name')

    parser.add_argument('--batch_size', type=int, default=4, help='The size of batch size')
    parser.add_argument('--print_freq', type=int, default=2000, help='The number of image_print_freq')
    parser.add_argument('--save_freq', type=int, default=10000, help='The number of ckpt_save_freq')

    parser.add_argument('--n_total_image', type=int, default=6400, help='The total iterations')
    parser.add_argument('--config', type=str, default='config-f', help='config-e or config-f')
    parser.add_argument('--lazy_regularization', type=str2bool, default=True, help='lazy_regularization')

    parser.add_argument('--img_size', type=int, default=256, help='The size of image')

    parser.add_argument('--n_test', type=int, default=10, help='The number of images generated by the test phase')

    parser.add_argument('--checkpoint_dir', type=str, default='checkpoint',
                        help='Directory name to save the checkpoints')
    parser.add_argument('--result_dir', type=str, default='results',
                        help='Directory name to save the generated images')
    parser.add_argument('--log_dir', type=str, default='logs',
                        help='Directory name to save training logs')
    parser.add_argument('--sample_dir', type=str, default='samples',
                        help='Directory name to save the samples on training')

    return check_args(parser.parse_args())


"""checking arguments"""
def check_args(args):
    # --checkpoint_dir
    check_folder(args.checkpoint_dir)

    # --result_dir
    check_folder(args.result_dir)

    # --result_dir
    check_folder(args.log_dir)

    # --sample_dir
    check_folder(args.sample_dir)

    # --batch_size
    try:
        assert args.batch_size >= 1
    except:
        print('batch size must be larger than or equal to one')

    return args

"""main"""
def main():

    args = vars(parse_args())

    # network params
    img_size = args['img_size']
    resolutions = [4, 8, 16, 32, 64, 128, 256, 512, 1024]
    if args['config'] == 'config-f':
        featuremaps = [512, 512, 512, 512, 512, 256, 128, 64, 32]  # config-f
    else:
        featuremaps = [512, 512, 512, 512, 256, 128, 64, 32, 16] # config-e
    train_resolutions, train_featuremaps = filter_resolutions_featuremaps(resolutions, featuremaps, img_size)
    g_params = {
        'z_dim': 512,
        'w_dim': 512,
        'labels_dim': 0,
        'n_mapping': 8,
        'resolutions': train_resolutions,
        'featuremaps': train_featuremaps,
        'w_ema_decay': 0.995,
        'style_mixing_prob': 0.9,
    }
    d_params = {
        'labels_dim': 0,
        'resolutions': train_resolutions,
        'featuremaps': train_featuremaps,
    }

    strategy = tf.distribute.MirroredStrategy()
    NUM_GPUS = strategy.num_replicas_in_sync
    batch_size = args['batch_size'] * NUM_GPUS  # global batch size

    # training parameters
    training_parameters = {
        # global params
        **args,

        # network params
        'g_params': g_params,
        'd_params': d_params,

        # training params
        'g_opt': {'learning_rate': 0.002, 'beta1': 0.0, 'beta2': 0.99, 'epsilon': 1e-08, 'reg_interval': 4},
        'd_opt': {'learning_rate': 0.002, 'beta1': 0.0, 'beta2': 0.99, 'epsilon': 1e-08, 'reg_interval': 16},
        'batch_size': batch_size,
        'NUM_GPUS' : NUM_GPUS,
        'n_samples': 4,
    }

    # automatic_gpu_usage()
    with strategy.scope():
        gan = StyleGAN2(training_parameters, strategy)

        # build graph
        gan.build_model()


        if args['phase'] == 'train' :
            gan.train()
            # gan.test_70000() # for FID evaluation ...
            print(" [*] Training finished!")

        if args['phase'] == 'test':
            gan.test()
            print(" [*] Test finished!")

        if args['phase'] == 'draw':

            if args['draw'] == 'style_mix':

                gan.draw_style_mixing_figure()

                print(" [*] Style mix finished!")


            elif args['draw'] == 'truncation_trick':

                gan.draw_truncation_trick_figure()

                print(" [*] Truncation_trick finished!")


            else:
                gan.draw_uncurated_result_figure()

                print(" [*] Un-curated finished!")



if __name__ == '__main__':
    main()