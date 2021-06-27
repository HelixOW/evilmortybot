import king
import sys

if __name__ == '__main__':
    if len(sys.argv) == 1:
        king.start_up_bot()

    if sys.argv[1] == "prod":
        king.start_up_bot()
    else:
        king.start_up_bot(token_path="data/beta_token.txt", _is_beta=True)
